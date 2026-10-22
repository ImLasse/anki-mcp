"""Explicit, revisioned local sources; never invents or verifies citations."""

import html
from urllib.parse import urlsplit
from .registry import tool, S, I, B, O, arr, obj, ToolError, validate
from .api import page
from .state import now
from .tools_notes import PAGING

SOURCE = obj(
    {
        "title": S,
        "authors": arr(S, 100),
        "url": S,
        "isbn": S,
        "edition": S,
        "year": {"type": "integer", "minimum": 1000, "maximum": 9999},
        "locator": S,
        "accessed": S,
        "summary": S,
    },
    ("title",),
)


def valid_source(data):
    validate(data, SOURCE)
    if not data["title"].strip():
        raise ToolError("Source title must not be empty")
    if data.get("url") and urlsplit(data["url"]).scheme.lower() not in ("http", "https"):
        raise ToolError("Source URL must use https:// or http://")


@tool(
    "create_source",
    "Register a user-provided citation locally, with revision tracking. Does not fetch or verify its content. Stored outside Anki sync; export_workspace backs up sources and links.",
    {"source": SOURCE},
    ("source",),
    write=True,
    undoable=False,
)
def create(s, source):
    valid_source(source)
    return s.store.put("source", {"citation": source, "revision": 1, "created": now(), "updated": now()})


@tool(
    "update_source",
    "Replace a citation with a new revision. Linked notes become needs_review until explicitly acknowledged; existing note content is never silently rewritten.",
    {"source_id": S, "source": SOURCE},
    ("source_id", "source"),
    write=True,
    undoable=False,
)
def update(s, source_id, source):
    valid_source(source)
    old = s.store.get("source", source_id)
    old.update(citation=source, revision=old["revision"] + 1, updated=now())
    return s.store.put("source", old, source_id)


@tool(
    "list_sources",
    "Read structured local source records, optionally filtered by title/authors text. Source records are user-provided, not verified.",
    {"query": S, **PAGING},
)
def sources(s, query="", offset=0, limit=100):
    import json

    return page(
        [x for x in s.store.objects("source") if query.casefold() in json.dumps(x["citation"], ensure_ascii=False).casefold()],
        offset,
        limit,
    )


@tool(
    "link_source",
    "Link explicit notes to the current source revision. Optional citation_field appends an escaped citation to that existing Anki field, so the text syncs with Anki. Local links do not sync. A changed source still needs review before acknowledge_source_review.",
    {"source_id": S, "note_ids": arr(I, 200), "locator": S, "citation_field": S},
    ("source_id", "note_ids"),
    write=True,
)
def link(s, source_id, note_ids, locator="", citation_field=None):
    source = s.store.get("source", source_id)
    notes = s.notes(note_ids)
    if citation_field and any(citation_field not in note for note in notes):
        raise ToolError("citation_field must exist on every selected note")
    citation = source["citation"]
    text = "; ".join(str(citation[x]) for x in ("title", "edition", "year", "url") if citation.get(x))
    if locator or citation.get("locator"):
        text += "; " + (locator or citation["locator"])
    results = []
    for note in notes:
        key = source_id + ":" + str(note.id)
        existing = next((x for x in s.store.objects("source_link") if x["id"] == key), None)
        if citation_field:
            value = '<div class="anki-mcp-citation">' + html.escape(text) + "</div>"
            if value not in note[citation_field]:
                note[citation_field] += ("\n" if note[citation_field] else "") + value
                s.col.update_note(note)
        reviewed = existing["reviewed_revision"] if existing else source["revision"]
        results.append(
            s.store.put(
                "source_link",
                {"source_id": source_id, "note_id": note.id, "locator": locator, "reviewed_revision": reviewed, "linked": now()},
                key,
            )
        )
    return results


@tool(
    "source_notes",
    "List linked notes and needs_review flags after source revisions. Missing/deleted notes remain visible for cleanup. Does not judge medical accuracy.",
    {"source_id": S, "needs_review_only": B, **PAGING},
    ("source_id",),
)
def linked(s, source_id, needs_review_only=False, offset=0, limit=100):
    source = s.store.get("source", source_id)
    results = []
    for item in s.store.objects("source_link"):
        if item["source_id"] != source_id:
            continue
        item["needs_review"] = item["reviewed_revision"] != source["revision"]
        item["current_revision"] = source["revision"]
        try:
            item["note"] = s.note_data(s.col.get_note(item["note_id"]))
            item["missing_note"] = False
        except Exception:
            item["note"] = None
            item["missing_note"] = True
        if not needs_review_only or item["needs_review"]:
            results.append(item)
    return page(results, offset, limit)


@tool(
    "acknowledge_source_review",
    "After the user has checked linked notes against a changed source, mark them reviewed at the current revision. Does not rewrite card content or verify it.",
    {"source_id": S, "note_ids": arr(I, 200), "confirm": B},
    ("source_id", "note_ids", "confirm"),
    write=True,
    destructive=True,
    undoable=False,
)
def acknowledge(s, source_id, note_ids, confirm):
    source = s.store.get("source", source_id)
    links = [s.store.get("source_link", source_id + ":" + str(nid)) for nid in note_ids]
    for item in links:
        item.update(reviewed_revision=source["revision"], reviewed=now())
        s.store.put("source_link", item, item["id"])
    return {"reviewed": len(links), "revision": source["revision"]}


@tool(
    "export_workspace",
    "Export local source records, source links and saved exam requests as JSON. Journal and temporary change plans are excluded. Treat exported note IDs as collection-specific. Save this response to back up or transfer metadata.",
)
def export(s):
    return {
        "format": "anki-mcp-workspace-1",
        "sources": s.store.objects("source"),
        "links": s.store.objects("source_link"),
        "exams": s.store.objects("exam"),
    }


@tool(
    "import_workspace",
    "Import a previously exported workspace into the same collection/profile on another machine. Merges by ID, replacing those records. Validate collection identity yourself: note IDs can refer to different notes in a different collection. Journal is not imported.",
    {"data": O, "confirm": B},
    ("data", "confirm"),
    write=True,
    destructive=True,
    undoable=False,
)
def import_workspace(s, data, confirm):
    from .registry import TOOLS

    if set(data) != {"format", "sources", "links", "exams"} or data["format"] != "anki-mcp-workspace-1":
        raise ToolError("Unsupported workspace format")
    if any(not isinstance(data[k], list) or len(data[k]) > 10000 for k in ("sources", "links", "exams")):
        raise ToolError("Expected lists with at most 10000 records each")
    known = {x["id"]: x for x in s.store.objects("source")}
    for item in data["sources"]:
        validate(
            item,
            obj(
                {"id": S, "citation": SOURCE, "revision": I, "created": S, "updated": S},
                ("id", "citation", "revision", "created", "updated"),
            ),
        )
        valid_source(item["citation"])
        known[item["id"]] = item
    for item in data["links"]:
        validate(
            item,
            obj(
                {"id": S, "source_id": S, "note_id": I, "locator": S, "reviewed_revision": I, "linked": S, "reviewed": S},
                ("id", "source_id", "note_id", "locator", "reviewed_revision", "linked"),
            ),
        )
        if item["source_id"] not in known or item["id"] != item["source_id"] + ":" + str(item["note_id"]):
            raise ToolError("Invalid source link")
        s.notes([item["note_id"]])
    for item in data["exams"]:
        validate(item, obj({"id": S, "name": S, "request": O, "last_estimate": O}, ("id", "name", "request", "last_estimate")))
        validate(item["request"], TOOLS["exam_plan"].schema)
    # Validate everything before one atomic metadata transaction.
    import json

    with s.store.db() as db:
        for key, kind in [("sources", "source"), ("links", "source_link"), ("exams", "exam")]:
            for item in data[key]:
                db.execute("insert or replace into objects values(?,?,?)", (kind, item["id"], json.dumps(item, ensure_ascii=False)))
    return {key: len(data[key]) for key in ("sources", "links", "exams")}
