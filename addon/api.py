"""Collection service. The desktop adapter calls it exclusively on Qt's main thread."""

import copy
from pathlib import Path
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError
from anki.errors import NotFoundError, InvalidInput
from google.protobuf.message import Message
from .registry import TOOLS, ToolError, validate


def plain(value):
    if isinstance(value, Message):
        return MessageToDict(value, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def patch(original, updates):
    """Strict recursive patch; unknown keys are rejected by protobuf separately."""
    result = copy.deepcopy(original)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = patch(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def patch_message(message, updates):
    data = patch(plain(message), updates)
    try:
        return ParseDict(data, type(message)(), ignore_unknown_fields=False)
    except (ValueError, TypeError, ParseError) as exc:
        raise ToolError("Invalid native settings patch: " + str(exc)) from exc


def page(items, offset=0, limit=100):
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "next_offset": offset + limit if offset + limit < len(items) else None,
    }


class Service:
    def __init__(self, collection, files_dir, *, read_only=False, ui=None):
        self.col = collection
        self.files_dir = Path(files_dir)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.read_only, self.ui = read_only, ui

    def execute(self, name, args):
        if name not in TOOLS:
            raise ToolError("Unknown tool")
        spec = TOOLS[name]
        validate(args, spec.schema)
        if spec.write and self.read_only:
            raise ToolError("Add-on is configured read_only")
        if spec.destructive and args.get("confirm") is not True:
            raise ToolError("Inspect the targets first, then pass confirm=true")
        undo = self.col.add_custom_undo_entry("MCP: " + name) if spec.write and spec.undoable else None
        try:
            return plain(spec.function(self, **args))
        except InvalidInput as exc:
            raise ToolError(str(exc)[:2048]) from exc
        except NotFoundError as exc:
            raise ToolError("Requested Anki object was not found") from exc
        finally:
            if undo is not None:
                self.col.merge_undo_entries(undo)
            if spec.write and self.ui:
                self.ui.reset()

    def deck(self, deck_id):
        result = self.col.decks.get(deck_id, default=False)
        if result is None:
            raise ToolError("Deck not found")
        return copy.deepcopy(result)

    def model(self, notetype_id):
        model = self.col.models.get(notetype_id)
        if model is None:
            raise ToolError("Note type not found")
        return copy.deepcopy(model)

    def notes(self, ids):
        return [self.col.get_note(nid) for nid in dict.fromkeys(ids)]

    def cards(self, ids):
        return [self.col.get_card(cid) for cid in dict.fromkeys(ids)]

    def file(self, filename, *, media=False, exists=False):
        if not filename or filename in (".", "..") or any(x in filename for x in ("/", "\\", "\x00", ":")):
            raise ToolError("Expected a plain filename without directories")
        root = Path(self.col.media.dir()) if media else self.files_dir
        path = root / filename
        if path.is_symlink() or path.resolve().parent != root.resolve():
            raise ToolError("Invalid file path")
        if exists and not path.is_file():
            raise ToolError("File not found")
        return path

    def note_data(self, note):
        return {
            "id": note.id,
            "guid": note.guid,
            "notetype_id": note.mid,
            "fields": dict(note.items()),
            "tags": list(note.tags),
            "card_ids": note.card_ids(),
            "modified": note.mod,
        }

    def card_data(self, card, render=False):
        result = {
            key: getattr(card, key)
            for key in (
                "id",
                "nid",
                "did",
                "ord",
                "type",
                "queue",
                "due",
                "ivl",
                "factor",
                "reps",
                "lapses",
                "left",
                "odue",
                "odid",
                "flags",
                "mod",
                "desired_retention",
                "decay",
                "last_review_time",
            )
        }
        result["memory_state"] = plain(card.memory_state) if card.memory_state is not None else None
        result["flag"] = card.user_flag()
        if render:
            result.update(question=card.question(), answer=card.answer(), css=card.note_type()["css"])
        return result


# Import modules after Service exists; decorators register all public tools.
from . import tools_collection, tools_notes, tools_learning, tools_media  # noqa: E402,F401
