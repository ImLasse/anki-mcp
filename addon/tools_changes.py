"""Persistent diffs, stale-state protection and change history."""

import copy
from datetime import datetime, timedelta, timezone
from .api import plain, patch_message
from .registry import TOOLS, tool, S, B, O, arr, obj, validate, ToolError
from .state import digest, now, snapshot
from .tools_notes import PAGING

ALLOWED = {"update_notes", "edit_tags", "schedule_cards", "rename_deck", "update_deck", "set_deck_options", "assign_deck_preset"}
CALL = obj({"tool": S, "arguments": O}, ("tool", "arguments"))


def targets(s, call):
    # Counts are useful for a journal but unrelated additions must not invalidate a reviewed plan.
    state = snapshot(s, call["tool"], call["arguments"])
    state.pop("note_count")
    state.pop("card_count")
    return state


def differences(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            result += differences(before.get(key), after.get(key), f"{path}.{key}" if path else key)
        return result
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def proposed(s, call, before):
    name, args = call["tool"], call["arguments"]
    after = copy.deepcopy(before)
    if name == "update_notes":
        for update in args["updates"]:
            note = after["notes"][str(update["note_id"])]
            if note is None:
                raise ToolError("Note not found")
            for field, value in update.get("fields", {}).items():
                if field not in note["fields"]:
                    raise ToolError("Unknown field: " + field)
                note["fields"][field] = value
            if "tags" in update:
                if any(not t.strip() or any(c.isspace() for c in t) for t in update["tags"]):
                    raise ToolError("Each tag must be nonempty and contain no whitespace")
                note["tags"] = update["tags"]
    elif name == "edit_tags":
        tags = args["tags"]
        if any(not t.strip() or any(c.isspace() for c in t) or any(c in t for c in "*?[]\\") for t in tags):
            raise ToolError("Change plans require literal, nonempty tags without whitespace or wildcards")
        for note in after["notes"].values():
            if note is None:
                raise ToolError("Note not found")
            old = note["tags"]
            if args["action"] == "add":
                note["tags"] = old + [t for t in tags if t.casefold() not in {x.casefold() for x in old}]
            else:
                note["tags"] = [
                    t for t in old if not any(t.casefold() == x.casefold() or t.casefold().startswith(x.casefold() + "::") for x in tags)
                ]
    elif name == "schedule_cards":
        if args["action"] not in ("move", "flag", "suspend", "unsuspend", "bury", "unbury"):
            raise ToolError("Plans support moving, flags, suspension and burying; other scheduling actions use native tools directly")
        if args["action"] == "move":
            if not args.get("deck_id") or s.deck(args["deck_id"])["dyn"]:
                raise ToolError("A normal target deck_id is required")
        if args["action"] == "flag" and "flag" not in args:
            raise ToolError("flag required")
        for card in after["cards"].values():
            if card is None:
                raise ToolError("Card not found")
            if args["action"] == "move":
                card["did"] = args["deck_id"]
            elif args["action"] == "flag":
                card["flag"] = args["flag"]
            else:
                card["planned_scheduler_action"] = args["action"]
    elif name == "rename_deck":
        if not args["name"].strip():
            raise ToolError("Deck name must not be empty")
        deck = s.deck(args["deck_id"])
        children = [d for d in s.col.decks.get_all_legacy() if d["name"].startswith(deck["name"] + "::")]
        if children:
            raise ToolError("Rename decks with children directly after inspecting the full hierarchy")
        after["decks"][str(args["deck_id"])]["name"] = args["name"]
    elif name == "update_deck":
        deck = s.deck(args["deck_id"])
        allowed = {"desc", "dailyLimits", "newLimit", "reviewLimit", "newLimitToday", "reviewLimitToday", "desiredRetention"}
        if set(args["patch"]) - allowed or set(args["patch"]) - deck.keys():
            raise ToolError("Unsupported deck property; inspect get_deck")
        after["decks"][str(args["deck_id"])].update(args["patch"])
    elif name == "set_deck_options":
        state = s.col.decks.get_deck_configs_for_update(args["deck_id"])
        current = next(x.config for x in state.all_config if x.config.id == state.current_deck.config_id)
        updated = plain(patch_message(current.config, args["patch"]))
        after["requested_preset_options"] = updated
        before["requested_preset_options"] = plain(current.config)
        after["preset_scope"] = "shared preset" if args.get("shared", False) else "new preset for this deck"
        affected = (
            [d["id"] for d in s.col.decks.get_all_legacy() if d.get("conf") == current.id] if args.get("shared") else [args["deck_id"]]
        )
        after["affected_deck_ids"] = affected
        if args.get("limits") is not None:
            before["requested_limits"] = plain(state.current_deck.limits)
            after["requested_limits"] = plain(patch_message(state.current_deck.limits, args["limits"]))
        if "global_fsrs" in args:
            before["global_fsrs"] = state.fsrs
            after["global_fsrs"] = args["global_fsrs"]
    elif name == "assign_deck_preset":
        if s.deck(args["deck_id"])["dyn"] or s.col.decks.get_config(args["preset_id"]) is None:
            raise ToolError("Preset not found")
        after["decks"][str(args["deck_id"])]["conf"] = args["preset_id"]
    return differences(before, after)


@tool(
    "plan_changes",
    "Create a persistent, reviewable before/after plan for existing notes, tags, cards and deck settings. Does not change the collection. At most 20 calls; each target may appear in only one call. Scheduler changes show the requested action; native scheduling determines final state. Apply with apply_change_plan.",
    {"calls": arr(CALL, 20)},
    ("calls",),
    write=True,
    undoable=False,
)
def plan(s, calls):
    states = []
    previews = []
    used = set()
    for call in calls:
        if call["tool"] not in ALLOWED:
            raise ToolError("Unsupported planned operation: " + call["tool"])
        validate(call["arguments"], TOOLS[call["tool"]].schema)
        if TOOLS[call["tool"]].destructive and not call["arguments"].get("confirm"):
            raise ToolError("Destructive planned calls require confirm=true inside arguments as well")
        state = targets(s, call)
        if len(calls) > 1 and call["tool"] in ("rename_deck", "update_deck", "set_deck_options", "assign_deck_preset"):
            raise ToolError("Review deck and preset changes in a separate one-call plan to avoid shared configuration interactions")
        if any(k.endswith("_truncated") for k in state):
            raise ToolError("At most 200 explicit targets per planned call")
        for category in ("notes", "cards", "decks"):
            for object_id in state.get(category, {}):
                key = (category, object_id)
                if key in used:
                    raise ToolError("Combine changes for the same target into a single call")
                used.add(key)
        states.append(copy.deepcopy(state))
        previews.append({"tool": call["tool"], "changes": proposed(s, call, copy.deepcopy(state))})
    data = {
        "status": "draft",
        "created": now(),
        "expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "calls": calls,
        "states": states,
        "previews": previews,
    }
    result = s.store.put("plan", data)
    return {k: v for k, v in result.items() if k != "states"}


@tool(
    "apply_change_plan",
    "Apply a reviewed plan once. Rejects expired, already used or stale plans before changing anything. User must approve the displayed scope. Multiple native operations are grouped in one undo entry; an error may still have partial effects.",
    {"plan_id": S, "confirm": B},
    ("plan_id", "confirm"),
    write=True,
    destructive=True,
    undoable=False,
)
def apply(s, plan_id, confirm):
    data = s.store.get("plan", plan_id)
    if data["status"] != "draft":
        raise ToolError("Plan is not an unused draft")
    if datetime.now(timezone.utc) > datetime.fromisoformat(data["expires"]):
        raise ToolError("Plan has expired; create a new preview")
    if any(digest(targets(s, call)) != digest(old) for call, old in zip(data["calls"], data["states"])):
        raise ToolError("Targets changed after preview; create a new plan")
    data["status"] = "applying"
    s.store.put("plan", data, plan_id)
    results = []
    undo = s.col.add_custom_undo_entry("MCP: apply_change_plan")
    try:
        for call in data["calls"]:
            results.append(plain(TOOLS[call["tool"]].function(s, **call["arguments"])))
    except BaseException:
        data["status"] = "failed_may_have_partial_effects"
        s.store.put("plan", data, plan_id)
        raise
    finally:
        s.col.merge_undo_entries(undo)
    data["status"] = "applied"
    data["applied_at"] = now()
    s.store.put("plan", data, plan_id)
    return {"plan_id": plan_id, "status": "applied", "results": results}


@tool(
    "change_history",
    "Read the persistent per-profile MCP change journal. Without entry_id returns summaries; with entry_id includes bounded before/after snapshots. Covers MCP operations only, not manual GUI edits. pending means outcome may be unknown after a crash.",
    {"entry_id": S, **PAGING},
)
def history(s, entry_id=None, offset=0, limit=100):
    return s.store.history(offset, limit, entry_id)
