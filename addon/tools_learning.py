"""Learning state, review history, analytics, scheduling and native review."""

import time
from .api import plain
from .registry import tool, S, I, B, arr, enum, ToolError
from .tools_notes import PAGING


@tool(
    "card_statistics",
    "Full native per-card statistics: review logs, FSRS difficulty/stability/retrievability, intervals, lapses and timing.",
    {"card_ids": arr(I, 100)},
    ("card_ids",),
)
def card_stats(s, card_ids):
    s.cards(card_ids)
    return [
        {"card_id": cid, "statistics": plain(s.col.card_stats_data(cid)), "computed_memory": plain(s.col.compute_memory_state(cid))}
        for cid in card_ids
    ]


@tool(
    "review_history",
    "Paginated native review history for a card. Timestamps, ratings, elapsed times and scheduling details.",
    {"card_id": I, **PAGING},
    ("card_id",),
)
def history(s, card_id, offset=0, limit=100):
    from .api import page

    s.cards([card_id])
    return page([plain(x) for x in s.col.get_review_logs(card_id)], offset, limit)


@tool(
    "learning_statistics",
    "Native Anki graphs for any search: review counts/time, intervals, card counts, answer ratings, FSRS retention/stability/difficulty and forecast. days=0 means all history.",
    {"query": S, "days": {"type": "integer", "minimum": 0, "maximum": 36500}},
)
def stats(s, query="", days=30):
    return s.col._backend.graphs(search=query, days=days)


@tool(
    "learning_overview",
    "Study dashboard for a search: total/new/learning/review, due, suspended, buried, leeches, mature cards, repeated lapses and forecast by day. Counts are independent (some overlap).",
    {"query": S, "forecast_days": {"type": "integer", "minimum": 1, "maximum": 365}},
)
def overview(s, query="", forecast_days=14):
    prefix = f"({query}) " if query.strip() else ""
    queries = {
        "total": "",
        "new": "is:new",
        "learning": "is:learn",
        "review": "is:review",
        "due": "is:due",
        "suspended": "is:suspended",
        "buried": "is:buried",
        "leeches": "tag:leech",
        "mature": "prop:ivl>=21",
        "repeated_lapses": "prop:lapses>=3",
    }
    counts = {key: len(s.col.find_cards((prefix + suffix).strip())) for key, suffix in queries.items()}
    forecast = [
        {"day_offset": day, "cards": len(s.col.find_cards(f"{prefix}is:review -is:suspended -is:buried prop:due={day}"))}
        for day in range(forecast_days)
    ]
    return {
        "counts": counts,
        "forecast": forecast,
        "scheduler_day": s.col.sched.today,
        "forecast_note": "Scheduled review cards only, excludes learning steps and future answers; today excludes overdue cards. due includes overdue.",
    }


@tool(
    "schedule_cards",
    "Suspend, unsuspend, bury, unbury, move, flag, set due dates, forget or reposition explicit cards. Forget resets scheduling; confirm required for all actions. Uses native scheduler.",
    {
        "card_ids": arr(I),
        "action": enum("suspend", "unsuspend", "bury", "unbury", "move", "flag", "set_due", "forget", "reposition"),
        "deck_id": I,
        "flag": {"type": "integer", "minimum": 0, "maximum": 7},
        "days": S,
        "reset_counts": B,
        "start": {"type": "integer", "minimum": 0},
        "step": I,
        "randomize": B,
        "shift_existing": B,
        "confirm": B,
    },
    ("card_ids", "action", "confirm"),
    write=True,
    destructive=True,
)
def schedule(
    s,
    card_ids,
    action,
    confirm,
    deck_id=None,
    flag=None,
    days=None,
    reset_counts=False,
    start=1,
    step=1,
    randomize=False,
    shift_existing=False,
):
    s.cards(card_ids)
    scheduler = s.col.sched
    direct = {
        "suspend": scheduler.suspend_cards,
        "unsuspend": scheduler.unsuspend_cards,
        "bury": scheduler.bury_cards,
        "unbury": scheduler.unbury_cards,
    }
    if action in direct:
        return direct[action](card_ids)
    if action == "move":
        if not deck_id or s.deck(deck_id)["dyn"]:
            raise ToolError("Provide a normal target deck_id")
        return s.col.set_deck(card_ids, deck_id)
    if action == "flag":
        if flag is None:
            raise ToolError("flag required")
        return s.col.set_user_flag_for_cards(flag, card_ids)
    if action == "set_due":
        if not days:
            raise ToolError("days required, e.g. '3', '3-7' or '3!'")
        return scheduler.set_due_date(card_ids, days)
    if action == "forget":
        return scheduler.schedule_cards_as_new(card_ids, reset_counts=reset_counts)
    return scheduler.reposition_new_cards(card_ids, starting_from=start, step_size=step, randomize=randomize, shift_existing=shift_existing)


@tool(
    "review_queue",
    "Read the active deck's native review queue and next answer states, without answering cards.",
    {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
)
def queue(s, limit=1):
    return {"deck_id": s.col.decks.get_current_id(), "queue": plain(s.col.sched.get_queued_cards(fetch_limit=limit))}


@tool("select_deck", "Select active deck for the Anki reviewer. Does not submit answers.", {"deck_id": I}, ("deck_id",), write=True)
def select(s, deck_id):
    s.deck(deck_id)
    return s.col.decks.set_current(deck_id)


@tool(
    "answer_card",
    "Submit an actual review answer through Anki's scheduler and write review history. Only use when user explicitly requests reviewing. Rating 1=Again, 2=Hard, 3=Good, 4=Easy. Requires first card in active queue.",
    {
        "card_id": I,
        "rating": {"type": "integer", "minimum": 1, "maximum": 4},
        "milliseconds_taken": {"type": "integer", "minimum": 0, "maximum": 3600000},
        "confirm": B,
    },
    ("card_id", "rating", "milliseconds_taken", "confirm"),
    write=True,
    destructive=True,
)
def answer(s, card_id, rating, milliseconds_taken, confirm):
    from anki.scheduler_pb2 import CardAnswer

    queued = s.col.sched.get_queued_cards(fetch_limit=1)
    if not queued.cards or queued.cards[0].card.id != card_id:
        raise ToolError("Card is not first in the active queue; refresh review_queue")
    states = queued.cards[0].states
    new_state = [states.again, states.hard, states.good, states.easy][rating - 1]
    result = s.col.sched.answer_card(
        CardAnswer(
            card_id=card_id,
            current_state=states.current,
            new_state=new_state,
            rating=rating,
            answered_at_millis=int(time.time() * 1000),
            milliseconds_taken=milliseconds_taken,
        )
    )
    return {"changes": plain(result), "card": s.card_data(s.col.get_card(card_id))}


@tool(
    "custom_study_defaults", "Read native custom study defaults for a deck: limits, tags and study options.", {"deck_id": I}, ("deck_id",)
)
def custom_defaults(s, deck_id):
    s.deck(deck_id)
    return s.col.sched.custom_study_defaults(deck_id)


@tool(
    "custom_study",
    "Run native custom study: extend today's limits, study ahead, review forgotten cards, preview new cards, cram by tags. Request accepts native CustomStudyRequest JSON. Use custom_study_defaults first; confirm required.",
    {"request": {"type": "object"}, "confirm": B},
    ("request", "confirm"),
    write=True,
    destructive=True,
)
def custom_study(s, request, confirm):
    from anki.scheduler_pb2 import CustomStudyRequest
    from google.protobuf.json_format import ParseDict, ParseError

    try:
        parsed = ParseDict(request, CustomStudyRequest(), ignore_unknown_fields=False)
    except ParseError as exc:
        raise ToolError("Invalid CustomStudyRequest: " + str(exc)) from exc
    s.deck(parsed.deck_id)
    return s.col.sched.custom_study(parsed)


@tool(
    "fsrs_parameters",
    "Compute or evaluate native FSRS parameters from the matching review history without changing settings. Requires sufficient reviews; may take time. Apply computed parameters separately with set_deck_options(fsrs_params_6).",
    {"deck_id": I, "action": enum("compute", "evaluate"), "query": S, "ignore_before_ms": {"type": "integer", "minimum": 0}},
    ("deck_id", "action"),
)
def fsrs_params(s, deck_id, action, query=None, ignore_before_ms=0):
    deck = s.deck(deck_id)
    state = s.col.decks.get_deck_configs_for_update(deck_id)
    cfg = next(x.config.config for x in state.all_config if x.config.id == state.current_deck.config_id)
    if query is None:
        # Search by deck ID is not part of Anki search grammar; quote and escape the name.
        escaped = deck["name"].replace("\\", "\\\\").replace('"', '\\"')
        query = f'deck:"{escaped}"'
    if action == "evaluate":
        return s.col._backend.evaluate_params(
            search=query, ignore_revlogs_before_ms=ignore_before_ms, num_of_relearning_steps=len(cfg.relearn_steps)
        )
    return s.col._backend.compute_fsrs_params(
        search=query,
        current_params=cfg.fsrs_params_6,
        ignore_revlogs_before_ms=ignore_before_ms,
        num_of_relearning_steps=len(cfg.relearn_steps),
        health_check=True,
    )
