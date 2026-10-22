"""Search, rich notes, tags, rendered cards and note type conversion."""

from .api import page
from .registry import tool, S, I, B, arr, enum, obj, ToolError

PAGING = {"offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}
FIELDS = {"type": "object", "additionalProperties": S}
TAGS = {"type": "array", "items": S, "maxItems": 500}
NOTE = obj({"deck_id": I, "notetype_id": I, "fields": FIELDS, "tags": TAGS, "allow_duplicate": B}, ("deck_id", "notetype_id", "fields"))


def prepare_note(s, deck_id, notetype_id, fields, tags=None, allow_duplicate=False):
    deck = s.deck(deck_id)
    if deck["dyn"]:
        raise ToolError("Cannot add notes directly to a filtered deck")
    note = s.col.new_note(s.model(notetype_id))
    if set(fields) - set(note.keys()):
        raise ToolError("Unknown field names; inspect get_notetype")
    for key, value in fields.items():
        note[key] = value
    note.tags = tags or []
    status = note.dupeOrEmpty()
    if status == 1:
        raise ToolError("First field must contain text or media")
    if status == 2 and not allow_duplicate:
        raise ToolError("Duplicate note; set allow_duplicate=true explicitly")
    return note


@tool(
    "search",
    "Search existing cards or notes with full Anki browser syntax: deck:, tag:, is:due, is:suspended, prop:lapses>3, added:, rated:, etc. Paginated IDs.",
    {"query": S, "kind": enum("cards", "notes"), **PAGING},
    ("query",),
)
def search(s, query, kind="cards", offset=0, limit=100):
    ids = s.col.find_cards(query, order=True) if kind == "cards" else s.col.find_notes(query)
    return page(list(ids), offset, limit)


@tool("get_notes", "Read fields as HTML, tags, GUIDs and generated card IDs.", {"note_ids": arr(I)}, ("note_ids",))
def get_notes(s, note_ids):
    return [s.note_data(n) for n in s.notes(note_ids)]


@tool(
    "get_cards",
    "Read scheduling and FSRS memory state. render=true includes question/answer HTML and CSS. due units depend on queue; see docs.",
    {"card_ids": arr(I), "render": B},
    ("card_ids",),
)
def get_cards(s, card_ids, render=False):
    return [s.card_data(c, render) for c in s.cards(card_ids)]


@tool(
    "add_notes",
    "Create rich HTML notes with images (<img src=...>), audio/video ([sound:...]), cloze syntax and tags. Upload media first. Native Anki generates cards. Validates the whole batch before adding.",
    {"notes": arr(NOTE, 200)},
    ("notes",),
    write=True,
)
def add_notes(s, notes):
    prepared = [(prepare_note(s, **data), data["deck_id"]) for data in notes]
    seen = set()
    for (note, _), data in zip(prepared, notes):
        key = (note.mid, note.fields[0])
        if key in seen and not data.get("allow_duplicate", False):
            raise ToolError("Duplicate first field within batch")
        seen.add(key)
    from anki.collection import AddNoteRequest

    s.col.add_notes([AddNoteRequest(note=n, deck_id=did) for n, did in prepared])
    return [s.note_data(n) for n, _ in prepared]


@tool(
    "update_notes",
    "Patch named fields and optionally replace tags. Omitted fields/tags remain unchanged; all notes validated before saving.",
    {"updates": arr(obj({"note_id": I, "fields": FIELDS, "tags": TAGS}, ("note_id",)), 200)},
    ("updates",),
    write=True,
)
def update_notes(s, updates):
    if len({x["note_id"] for x in updates}) != len(updates):
        raise ToolError("Use one update per note")
    notes = []
    for data in updates:
        note = s.col.get_note(data["note_id"])
        for key, value in data.get("fields", {}).items():
            if key not in note:
                raise ToolError("Unknown field: " + key)
            note[key] = value
        if "tags" in data:
            note.tags = data["tags"]
        notes.append(note)
    s.col.update_notes(notes)
    return [s.note_data(n) for n in notes]


@tool(
    "delete_notes",
    "Delete notes and every card generated from them, including review history. confirm required.",
    {"note_ids": arr(I), "confirm": B},
    ("note_ids", "confirm"),
    write=True,
    destructive=True,
)
def delete_notes(s, note_ids, confirm):
    s.notes(note_ids)
    return s.col.remove_notes(note_ids)


@tool("list_tags", "Read all registered tags and their hierarchy.")
def tags(s):
    return {"tags": s.col.tags.all(), "tree": s.col.tags.tree()}


@tool(
    "edit_tags",
    "Add or remove tags on explicit note IDs. Supports hierarchical tags such as Medizin::Kardiologie.",
    {"note_ids": arr(I), "tags": arr(S), "action": enum("add", "remove")},
    ("note_ids", "tags", "action"),
    write=True,
)
def edit_tags(s, note_ids, tags, action):
    s.notes(note_ids)
    if any(not tag.strip() or any(c.isspace() for c in tag) for tag in tags):
        raise ToolError("Each tag must be nonempty and contain no whitespace")
    fn = s.col.tags.bulk_add if action == "add" else s.col.tags.bulk_remove
    return fn(note_ids, " ".join(tags))


@tool("rename_tag", "Rename a tag and all its children across the collection.", {"old": S, "new": S}, ("old", "new"), write=True)
def rename_tag(s, old, new):
    return s.col.tags.rename(old, new)


@tool(
    "remove_tag",
    "Remove a tag and its children from the entire collection. confirm required.",
    {"tag": S, "confirm": B},
    ("tag", "confirm"),
    write=True,
    destructive=True,
)
def remove_tag(s, tag, confirm):
    return s.col.tags.remove(tag)


@tool(
    "change_notetype",
    "Convert notes to a new note type using native field/template mapping. Maps are target-index -> source-index arrays; -1 means blank/new. May delete cards. Inspect types first.",
    {
        "note_ids": arr(I),
        "notetype_id": I,
        "field_map": arr({"type": "integer", "minimum": -1}, 100),
        "template_map": {"type": "array", "items": {"type": "integer", "minimum": -1}, "maxItems": 100},
        "confirm": B,
    },
    ("note_ids", "notetype_id", "field_map", "confirm"),
    write=True,
    destructive=True,
)
def convert(s, note_ids, notetype_id, field_map, confirm, template_map=None):
    from anki.notetypes_pb2 import ChangeNotetypeRequest

    notes = s.notes(note_ids)
    old_ids = {n.mid for n in notes}
    if len(old_ids) != 1:
        raise ToolError("All notes must have the same source type")
    old_id = next(iter(old_ids))
    old, new = s.model(old_id), s.model(notetype_id)
    if len(field_map) != len(new["flds"]) or any(i >= len(old["flds"]) for i in field_map):
        raise ToolError("field_map must map each target field to a valid source index or -1")
    cloze = bool(old["type"] or new["type"])
    template_map = [] if cloze else template_map
    if not cloze and (template_map is None or len(template_map) != len(new["tmpls"]) or any(i >= len(old["tmpls"]) for i in template_map)):
        raise ToolError("template_map must map each target template to a source index or -1")
    # Native API uses -1 for an unmapped source.
    req = ChangeNotetypeRequest(
        note_ids=note_ids,
        old_notetype_id=old_id,
        new_notetype_id=notetype_id,
        old_notetype_name=old["name"],
        new_fields=field_map,
        new_templates=template_map,
        current_schema=s.col.db.scalar("select scm from col"),
        is_cloze=cloze,
    )
    return s.col.models.change_notetype_of_notes(req)


@tool(
    "find_duplicates",
    "Find duplicate note field content within an Anki search (e.g. identify redundant medical facts).",
    {"field_name": S, "query": S, **PAGING},
    ("field_name",),
)
def duplicates(s, field_name, query="", offset=0, limit=100):
    return page(s.col.find_dupes(field_name, query), offset, limit)


@tool(
    "find_replace",
    "Native find/replace on explicit notes, optionally in one field. Supports regex and case matching. confirm required.",
    {"note_ids": arr(I), "search": S, "replacement": S, "field_name": S, "regex": B, "match_case": B, "confirm": B},
    ("note_ids", "search", "replacement", "confirm"),
    write=True,
    destructive=True,
)
def replace(s, note_ids, search, replacement, confirm, field_name=None, regex=False, match_case=False):
    s.notes(note_ids)
    return s.col.find_and_replace(
        note_ids=note_ids, search=search, replacement=replacement, field_name=field_name, regex=regex, match_case=match_case
    )


@tool(
    "empty_cards", "Report cards whose cloze, mask or template content was removed. Native Anki preserves these until explicitly deleted."
)
def empty_cards(s):
    return s.col.get_empty_cards()


@tool(
    "delete_cards",
    "Delete explicit individual cards and any resulting orphan notes. Removes review history. Useful after inspecting empty_cards; confirm required.",
    {"card_ids": arr(I), "confirm": B},
    ("card_ids", "confirm"),
    write=True,
    destructive=True,
)
def delete_cards(s, card_ids, confirm):
    s.cards(card_ids)
    return s.col.remove_cards_and_orphaned_notes(card_ids)


@tool(
    "usage_guide",
    "Read concrete Anki MCP workflows and examples. Call before image occlusion or custom note types. Explains localized fields, media, mask grouping, native vs third-party types and safe editing.",
    {"topic": enum("start", "image_occlusion", "notetypes", "learning", "media", "quality", "changes", "sources", "exam")},
    ("topic",),
)
def usage_guide(s, topic):
    import json
    from pathlib import Path

    guides = json.loads(Path(__file__).with_name("ai_guide.json").read_text(encoding="utf-8"))
    return {"topic": topic, "guide": guides[topic]}
