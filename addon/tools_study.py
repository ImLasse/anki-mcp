"""Bounded local similarity candidates and transparent exam budget estimates."""

from collections import Counter
from datetime import date, timedelta
import math
import re
import unicodedata
from .registry import tool, S, arr, obj, ToolError
from .tools_quality import FieldContent


@tool(
    "similar_notes",
    "Find local lexical overlap candidates for an Anki search using TF-IDF word and character features. Read-only, no automatic merging. Scores are not semantic equivalence or medical correctness: inspect both notes, especially negation, before recommending changes. At most 500 notes from the sorted search result.",
    {
        "query": S,
        "fields": arr(S, 100),
        "max_notes": {"type": "integer", "minimum": 2, "maximum": 500},
        "min_score": {"type": "number", "minimum": 0, "maximum": 1},
        "max_pairs": {"type": "integer", "minimum": 1, "maximum": 100},
    },
)
def similar(s, query="", fields=None, max_notes=200, min_score=0.55, max_pairs=20):
    ids = sorted(s.col.find_notes(query))
    selected = ids[:max_notes]
    texts = []
    vectors = []
    for note in s.notes(selected):
        content = " ".join(" ".join(FieldContent(value).text) for key, value in note.items() if fields is None or key in fields)
        content = unicodedata.normalize("NFKC", content).casefold()
        words = re.findall(r"\w+", content[:12000])
        joined = " ".join(words)
        counts = Counter("w:" + w for w in words)
        counts.update("c:" + joined[i : i + 4] for i in range(max(0, len(joined) - 3)))
        texts.append(content[:400])
        vectors.append(counts)
    freq = Counter(key for v in vectors for key in v)
    for index, v in enumerate(vectors):
        weighted = {key: (1 + math.log(count)) * (1 + math.log((1 + len(vectors)) / (1 + freq[key]))) for key, count in v.items()}
        norm = math.sqrt(sum(x * x for x in weighted.values())) or 1
        vectors[index] = {k: v / norm for k, v in weighted.items()}
    pairs = []
    for a, va in enumerate(vectors):
        for b in range(a + 1, len(vectors)):
            vb = vectors[b]
            small, large = (va, vb) if len(va) < len(vb) else (vb, va)
            score = sum(value * large.get(key, 0) for key, value in small.items())
            if score >= min_score:
                pairs.append({"note_ids": [selected[a], selected[b]], "score": round(min(score, 1), 4), "excerpts": [texts[a], texts[b]]})
    pairs.sort(key=lambda x: x["score"], reverse=True)
    return {
        "items": pairs[:max_pairs],
        "matching_pairs": len(pairs),
        "scanned": len(selected),
        "total": len(ids),
        "truncated": len(ids) > max_notes,
        "method": "Local TF-IDF words + character 4-grams; candidate retrieval, not semantic validation",
        "next_step": "Use get_notes to compare the full candidates and their sources; never delete based on this score alone.",
    }


TOPIC = obj({"name": S, "query": S}, ("name", "query"))


@tool(
    "exam_plan",
    "Estimate a daily study budget until an exam from a search, active new cards, currently scheduled reviews and topic counts. Does not change scheduling. Fixed per-card time assumptions are explicit; future answers, relearning and reviews of newly learned cards are not predicted, so reserve extra time.",
    {
        "query": S,
        "exam_date": S,
        "start_date": S,
        "daily_minutes": {"type": "integer", "minimum": 1, "maximum": 1440},
        "new_card_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
        "review_card_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
        "weekly_minutes": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 1440}, "minItems": 7, "maxItems": 7},
        "topics": arr(TOPIC, 30),
    },
    ("exam_date", "daily_minutes"),
)
def exam(
    s, exam_date, daily_minutes, query="", start_date=None, new_card_seconds=120, review_card_seconds=30, weekly_minutes=None, topics=None
):
    try:
        start = date.fromisoformat(start_date) if start_date else date.today()
        end = date.fromisoformat(exam_date)
    except ValueError as exc:
        raise ToolError("Dates must use YYYY-MM-DD") from exc
    if start < date.today() or not 1 <= (end - start).days <= 365:
        raise ToolError("Start must be today or later and exam must be 1–365 days after start")
    active = f"({query}) -is:suspended -is:buried" if query.strip() else "-is:suspended -is:buried"
    new = len(s.col.find_cards(active + " is:new"))
    remaining = new
    rows = []
    today = date.today()
    first_offset = (start - today).days
    overdue = len(s.col.find_cards(active + f" is:review prop:due<{first_offset}"))
    due_counts = []
    for index in range((end - start).days):
        offset = first_offset + index
        due_counts.append(len(s.col.find_cards(active + f" is:review prop:due={offset}")) + (overdue if index == 0 else 0))
    capacities = []
    for index, due in enumerate(due_counts):
        day = start + timedelta(days=index)
        minutes = weekly_minutes[day.weekday()] if weekly_minutes is not None else daily_minutes
        capacities.append(max(0, (minutes * 60 - due * review_card_seconds) // new_card_seconds))
    for index, due in enumerate(due_counts):
        day = start + timedelta(days=index)
        minutes = weekly_minutes[day.weekday()] if weekly_minutes is not None else daily_minutes
        # Spread work by remaining time capacity; never overbook a day's budget.
        future = sum(capacities[index:])
        allocated = min(remaining, capacities[index], math.ceil(remaining * capacities[index] / future) if future else 0)
        remaining -= allocated
        rows.append(
            {
                "date": day.isoformat(),
                "budget_minutes": minutes,
                "scheduled_reviews": due,
                "new_cards": allocated,
                "estimated_minutes": round((due * review_card_seconds + allocated * new_card_seconds) / 60, 1),
                "review_overload_minutes": round(max(0, due * review_card_seconds - minutes * 60) / 60, 1),
            }
        )
    topic_counts = [
        {
            "name": t["name"],
            "cards": len(s.col.find_cards(f"({active})" + (f" ({t['query']})" if t["query"].strip() else ""))),
            "new": len(s.col.find_cards(f"({active})" + (f" ({t['query']})" if t["query"].strip() else "") + " is:new")),
        }
        for t in topics or []
    ]
    return {
        "query": query,
        "exam_date": end.isoformat(),
        "new_cards": new,
        "unallocated_new_cards": remaining,
        "feasible_under_assumptions": remaining == 0 and not any(r["review_overload_minutes"] for r in rows),
        "days": rows,
        "topics": topic_counts,
        "assumptions": {
            "new_card_seconds": new_card_seconds,
            "review_card_seconds": review_card_seconds,
            "weekly_minutes_order": "Monday through Sunday",
            "excluded": "Learning steps, future answers, future repeats of new cards, buried/suspended cards; topic counts can overlap",
            "exam_day": "Not allocated; study days end the day before the exam",
            "today": "Machine local date; Anki due offsets use the scheduler day",
        },
    }


@tool(
    "save_exam_plan",
    "Save an exam-planning request locally for later recalculation. Not synced by Anki; use export_workspace for transfer. Does not alter cards.",
    {"name": S, "request": {"type": "object"}},
    ("name", "request"),
    write=True,
    undoable=False,
)
def save_exam(s, name, request):
    from .registry import TOOLS, validate

    validate(request, TOOLS["exam_plan"].schema)
    calculated = exam(s, **request)
    return s.store.put("exam", {"name": name, "request": request, "last_estimate": calculated})


@tool("saved_exam_plans", "Read locally saved exam requests. Recalculate with exam_plan to reflect current learning progress.")
def saved(s):
    return s.store.objects("exam")
