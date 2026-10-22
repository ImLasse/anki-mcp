"""Media, native image occlusion and controlled package transfer."""

import base64
import binascii
import html
from pathlib import Path
from .api import plain, page
from .registry import tool, S, I, B, O, arr, enum, obj, ToolError
from .tools_notes import PAGING, TAGS

MAX_FILE = 20 * 1024 * 1024


def decode(data):
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ToolError("Expected valid base64") from exc
    if len(raw) > MAX_FILE:
        raise ToolError("File exceeds 20 MiB")
    return raw


@tool(
    "store_media",
    "Store image, audio, video or other media from base64. Returns actual collision-safe filename and HTML/sound references. Never assumes requested filename was retained.",
    {"filename": S, "data_base64": S},
    ("filename", "data_base64"),
    write=True,
    undoable=False,
)
def store(s, filename, data_base64):
    s.file(filename, media=True)
    name = s.col.media.write_data(filename, decode(data_base64))
    return {"filename": name, "image_html": f'<img src="{html.escape(name, quote=True)}">', "sound_tag": f"[sound:{name}]"}


@tool(
    "read_media",
    "Read local collection media as base64 in chunks; no arbitrary filesystem access. Default chunk 1 MiB.",
    {"filename": S, "offset": {"type": "integer", "minimum": 0}, "length": {"type": "integer", "minimum": 1, "maximum": 4194304}},
    ("filename",),
)
def read_media(s, filename, offset=0, length=1048576):
    return read_chunk(s.file(filename, media=True, exists=True), offset, length)


def read_chunk(path, offset, length):
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(offset)
        raw = handle.read(length)
    return {
        "filename": path.name,
        "size": size,
        "offset": offset,
        "data_base64": base64.b64encode(raw).decode(),
        "next_offset": offset + len(raw) if offset + len(raw) < size else None,
    }


@tool("list_media", "List collection media, optionally filtered by filename substring.", {"contains": S, **PAGING})
def list_media(s, contains="", offset=0, limit=100):
    paths = Path(s.col.media.dir()).iterdir()
    return page(
        sorted(p.name for p in paths if p.is_file() and not p.is_symlink() and contains.casefold() in p.name.casefold()), offset, limit
    )


@tool(
    "check_media",
    "Native Anki missing/unused media report; may normalize filenames and take time on large collections.",
    write=True,
    undoable=False,
)
def check_media(s):
    return s.col.media.check()


@tool(
    "trash_media",
    "Move specified collection media into Anki media trash. Not covered by collection undo; restore with restore_media_trash.",
    {"filenames": arr(S), "confirm": B},
    ("filenames", "confirm"),
    write=True,
    destructive=True,
    undoable=False,
)
def trash_media(s, filenames, confirm):
    for name in filenames:
        s.file(name, media=True, exists=True)
    s.col.media.trash_files(filenames)
    return {"trashed": filenames}


@tool("restore_media_trash", "Restore Anki's media trash (all files).", write=True, undoable=False)
def restore_media(s):
    s.col.media.restore_trash()
    return {"restored": True}


RECT = obj(
    {
        "ordinal": I,
        "left": {"type": "number", "minimum": 0, "maximum": 1},
        "top": {"type": "number", "minimum": 0, "maximum": 1},
        "width": {"type": "number", "minimum": 0.000001, "maximum": 1},
        "height": {"type": "number", "minimum": 0.000001, "maximum": 1},
    },
    ("ordinal", "left", "top", "width", "height"),
)


def occlusion_text(occlusions=None, rectangles=None):
    if (occlusions is None) == (rectangles is None):
        raise ToolError("Provide exactly one of native occlusions or rectangles")
    if occlusions is not None:
        if not occlusions.strip():
            raise ToolError("Occlusion markup must not be empty")
        return occlusions
    result = []
    for r in rectangles:
        if r["left"] + r["width"] > 1.000001 or r["top"] + r["height"] > 1.000001:
            raise ToolError("Normalized rectangle exceeds image bounds")
        shape = ":".join(["image-occlusion", "rect"] + [f"{key}={r[key]:.6f}" for key in ("left", "top", "width", "height")])
        result.append("{{c" + str(r["ordinal"]) + "::" + shape + "}}")
    return "<br>".join(result)


@tool(
    "create_image_occlusion",
    "Create native Image Occlusion cards for anatomy/histology etc. Upload image first. Rectangles use normalized 0..1 coordinates and ordinal >=1; same ordinal groups masks on one card. Alternatively provide native cloze occlusions markup for ellipse/polygon/text and all advanced shapes.",
    {
        "deck_id": I,
        "filename": S,
        "notetype_id": I,
        "rectangles": arr(RECT, 500),
        "occlusions": S,
        "header": S,
        "back_extra": S,
        "tags": TAGS,
    },
    ("deck_id", "filename"),
    write=True,
)
def create_io(s, deck_id, filename, notetype_id=None, rectangles=None, occlusions=None, header="", back_extra="", tags=None):
    if s.deck(deck_id)["dyn"]:
        raise ToolError("Expected a normal deck")
    path = s.file(filename, media=True, exists=True)
    markup = occlusion_text(occlusions, rectangles)
    s.col.add_image_occlusion_notetype()
    if notetype_id is None:
        notetype_id = next(m["id"] for m in s.col.models.all() if m.get("originalStockKind") == 6)
    model = s.model(notetype_id)
    if model.get("originalStockKind") != 6:
        raise ToolError("Expected native Image Occlusion type")
    # Field ordinals belong to the native type, independent of translated field names.
    note = s.col.new_note(model)
    note.fields[0:4] = [markup, f'<img src="{html.escape(path.name, quote=True)}">', header, back_extra]
    note.tags = tags or []
    s.col.add_note(note, deck_id)
    return s.note_data(note)


@tool(
    "get_image_occlusion",
    "Read native parsed occlusion shapes, grouping and note metadata. Image bytes use read_media.",
    {"note_id": I},
    ("note_id",),
)
def get_io(s, note_id):
    result = s.col.get_image_occlusion_note(note_id)
    # Avoid embedding large image_data; returned separately by read_media.
    data = plain(result)
    if isinstance(data.get("note"), dict):
        data["note"].pop("image_data", None)
    return data


@tool(
    "update_image_occlusion",
    "Update native Image Occlusion masks and optional header/back/tags. Rebuilds generated cards using Anki. Pass rectangles OR native occlusions to change masks.",
    {"note_id": I, "rectangles": arr(RECT), "occlusions": S, "header": S, "back_extra": S, "tags": TAGS},
    ("note_id",),
    write=True,
)
def update_io(s, note_id, rectangles=None, occlusions=None, header=None, back_extra=None, tags=None):
    note = s.col.get_note(note_id)
    if s.model(note.mid).get("originalStockKind") != 6:
        raise ToolError("Expected native Image Occlusion note")
    markup = occlusion_text(occlusions, rectangles) if rectangles is not None or occlusions is not None else None
    return s.col.update_image_occlusion_note(note_id, markup, header, back_extra, tags)


@tool(
    "transfer_file",
    "Upload/download/list/delete staged .apkg files in the add-on's user_files/transfers folder. Upload chunks with offset (max 20 MiB per chunk, 512 MiB file). offset=0 creates a NEW file; delete first to replace. Never reads arbitrary paths.",
    {
        "action": enum("upload", "download", "list", "delete"),
        "filename": S,
        "data_base64": S,
        "offset": {"type": "integer", "minimum": 0},
        "length": {"type": "integer", "minimum": 1, "maximum": 4194304},
        "confirm": B,
    },
    ("action",),
    write=True,
    undoable=False,
)
def transfer(s, action, filename=None, data_base64=None, offset=0, length=1048576, confirm=False):
    if action == "list":
        return [
            {"filename": p.name, "size": p.stat().st_size} for p in sorted(s.files_dir.glob("*.apkg")) if p.is_file() and not p.is_symlink()
        ]
    if not filename or not filename.endswith(".apkg"):
        raise ToolError("An .apkg filename is required")
    path = s.file(filename, exists=action != "upload")
    if action == "download":
        return read_chunk(path, offset, length)
    if action == "delete":
        if not confirm:
            raise ToolError("confirm=true required")
        path.unlink()
        return {"deleted": filename}
    if data_base64 is None:
        raise ToolError("data_base64 required")
    raw = decode(data_base64)
    if offset + len(raw) > 512 * 1024 * 1024:
        raise ToolError("Staged package exceeds 512 MiB")
    if offset == 0:
        mode = "xb"
    else:
        if not path.is_file() or path.stat().st_size != offset:
            raise ToolError("offset must match current staged file length")
        mode = "ab"
    try:
        with path.open(mode) as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise ToolError("Staged file already exists; choose another name or delete it explicitly") from exc
    return {"filename": filename, "size": path.stat().st_size}


@tool(
    "export_package",
    "Export a deck (including children) or entire collection to a staged .apkg, with media, scheduling and deck configs. Download with transfer_file. Does not close the collection.",
    {"filename": S, "deck_id": I, "include_media": B, "include_scheduling": B},
    ("filename",),
    write=True,
    undoable=False,
)
def export_package(s, filename, deck_id=None, include_media=True, include_scheduling=True):
    from anki.import_export_pb2 import ExportAnkiPackageOptions
    from anki.collection import DeckIdLimit

    if not filename.endswith(".apkg"):
        raise ToolError("Expected .apkg extension")
    path = s.file(filename)
    if path.exists():
        raise ToolError("Output already exists; choose a new filename")
    if deck_id is not None:
        s.deck(deck_id)
    options = ExportAnkiPackageOptions(with_scheduling=include_scheduling, with_deck_configs=True, with_media=include_media)
    count = s.col.export_anki_package(out_path=str(path), options=options, limit=DeckIdLimit(deck_id) if deck_id is not None else None)
    return {"filename": filename, "exported": count, "size": path.stat().st_size}


@tool(
    "import_package",
    "Import a staged .apkg through Anki's native importer, including media, tags and optional scheduling. Native importer options can be provided. Not covered by collection undo; backup first.",
    {"filename": S, "options": O, "confirm": B},
    ("filename", "confirm"),
    write=True,
    destructive=True,
    undoable=False,
)
def import_package(s, filename, confirm, options=None):
    from anki.import_export_pb2 import ImportAnkiPackageRequest
    from google.protobuf.json_format import ParseDict

    if not filename.endswith(".apkg"):
        raise ToolError("Expected .apkg")
    path = s.file(filename, exists=True)
    req = ImportAnkiPackageRequest(package_path=str(path))
    if options is not None:
        ParseDict(options, req.options, ignore_unknown_fields=False)
    return s.col.import_anki_package(req)


@tool(
    "create_backup",
    "Create a native collection backup in add-on user_files/backups. Media are excluded by Anki; export_package includes them. Backup files are not sent to the model.",
    write=True,
    undoable=False,
)
def backup(s):
    directory = s.files_dir.parent / "backups"
    directory.mkdir(exist_ok=True)
    created = s.col.create_backup(backup_folder=str(directory), force=True, wait_for_completion=True)
    return {"created": created, "includes_media": False}


@tool(
    "get_image",
    "View an existing collection image as actual MCP image content for vision-capable clients. Use before placing occlusion masks. Supports PNG/JPEG/GIF/WebP, maximum 4 MiB; SVG/PDF must be converted by the client first.",
    {"filename": S},
    ("filename",),
)
def get_image(s, filename):
    from .registry import ContentResult

    path = s.file(filename, media=True, exists=True)
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ToolError("Image exceeds 4 MiB. Resize it with the client's image tools before uploading")
    raw = path.read_bytes()
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif raw.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif raw[:6] in (b"GIF87a", b"GIF89a"):
        mime = "image/gif"
    elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ToolError("Expected PNG, JPEG, GIF or WebP image bytes")
    return ContentResult(
        [
            {"type": "text", "text": "Collection image: " + filename},
            {"type": "image", "data": base64.b64encode(raw).decode(), "mimeType": mime},
        ]
    )
