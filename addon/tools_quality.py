"""Read-only note previews and technical quality checks for study collections."""

import copy
from html.parser import HTMLParser
import re
from urllib.parse import unquote
from .registry import tool, S, B, arr
from .tools_notes import NOTE, PAGING, prepare_note


class FieldContent(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.media = []
        self.hidden_depth = 0
        self.feed(value)
        self.media.extend(re.findall(r"\[sound:([^\]]+)\]", value))

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden_depth += 1
        attrs = dict(attrs)
        if tag in ("img", "audio", "video", "source") and attrs.get("src"):
            self.media.append(attrs["src"])

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth:
            self.text.append(data)

    def populated(self):
        return bool("".join(self.text).strip() or self.media)


@tool(
    "preview_notes",
    "Render proposed notes as native Anki question/answer HTML and CSS before saving. Does not add notes/cards. Standard note types preview every template; conditional templates may not generate a saved card. Cloze previews use actual cloze ordinals. Reports duplicates as warnings.",
    {"notes": arr(NOTE, 20)},
    ("notes",),
)
def preview_notes(s, notes):
    from anki.cards import Card
    from anki.template import TemplateRenderContext

    previews = []
    total_cards = 0
    seen = set()
    for data in notes:
        note = prepare_note(s, **{**data, "allow_duplicate": True})
        model = s.model(note.mid)
        ordinals = sorted({n - 1 for n in note.cloze_numbers_in_fields()}) if model["type"] else list(range(len(model["tmpls"])))
        total_cards += len(ordinals)
        if total_cards > 100:
            from .registry import ToolError

            raise ToolError("At most 100 cards can be previewed in one request")
        warnings = []
        key = (note.mid, note.fields[0])
        if key in seen:
            warnings.append("Duplicate first field within this proposed batch")
        seen.add(key)
        if note.dupeOrEmpty() == 2:
            warnings.append("Duplicate first field in an existing note")
        if model["type"] and not ordinals:
            warnings.append("No cloze ordinals found; add {{c1::...}} or native occlusion markup")
        if not model["type"]:
            warnings.append("All templates previewed; conditional templates may be omitted when cards are generated")
        cards = []
        for ordinal in ordinals:
            template = copy.deepcopy(model["tmpls"][0 if model["type"] else ordinal])
            template["ord"] = ordinal
            card = Card(s.col)
            card.did = data["deck_id"]
            card.ord = ordinal
            output = TemplateRenderContext.from_card_layout(note, card, model, template, fill_empty=False).render()
            cards.append(
                {
                    "ordinal": ordinal,
                    "template": template["name"],
                    "question": output.question_text,
                    "answer": output.answer_text,
                    "css": output.css,
                }
            )
        previews.append(
            {
                "deck_id": data["deck_id"],
                "deck_name": s.deck(data["deck_id"])["name"],
                "notetype_id": note.mid,
                "fields": dict(note.items()),
                "tags": list(note.tags),
                "cards": cards,
                "warnings": warnings,
            }
        )
    return {
        "saved": False,
        "notes": previews,
        "rendered_cards": total_cards,
        "renderer": "Native Anki card-layout preview; dynamic fields such as Deck may use placeholders",
    }


@tool(
    "audit_notes",
    "Technical note-quality audit for an Anki search: empty fields, missing local image/audio/video files, optional required/source fields and absent cloze markup. Paginated, read-only. Does not verify medical accuracy, authenticity of sources or remote URLs. required_fields use exact localized names.",
    {"query": S, "required_fields": {"type": "array", "items": S, "maxItems": 100}, "check_media": B, **PAGING},
)
def audit_notes(s, query="", required_fields=None, check_media=True, offset=0, limit=100):
    from .registry import ToolError

    ids = list(s.col.find_notes(query))
    selected = ids[offset : offset + limit]
    results = []
    for note in s.notes(selected):
        fields = dict(note.items())
        parsed = {key: FieldContent(value) for key, value in fields.items()}
        empty = [name for name, content in parsed.items() if not content.populated()]
        required = required_fields or []
        missing_fields = [name for name in required if name not in fields]
        empty_required = [name for name in required if name in empty]
        missing_media = []
        for field_name, content in parsed.items():
            if not check_media:
                continue
            for filename in dict.fromkeys(content.media):
                if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", filename) or filename.startswith("//"):
                    continue
                filename = unquote(filename)
                try:
                    s.file(filename, media=True, exists=True)
                except ToolError:
                    missing_media.append({"field": field_name, "filename": filename})
        model = s.model(note.mid)
        no_cloze = bool(model["type"] and not note.cloze_numbers_in_fields())
        issues = []
        if empty_required:
            issues.append("empty_required_fields")
        if missing_fields:
            issues.append("required_fields_not_in_notetype")
        if missing_media:
            issues.append("missing_local_media")
        if no_cloze:
            issues.append("no_cloze_markup")
        results.append(
            {
                "note_id": note.id,
                "notetype_id": note.mid,
                "empty_fields": empty,
                "empty_required_fields": empty_required,
                "unknown_required_fields": missing_fields,
                "missing_media": missing_media,
                "issues": issues,
            }
        )
    return {
        "items": results,
        "total": len(ids),
        "scanned": len(selected),
        "notes_with_issues": sum(bool(item["issues"]) for item in results),
        "next_offset": offset + limit if offset + limit < len(ids) else None,
        "scope": "Technical completeness only; not a check of medical correctness or source reliability",
    }
