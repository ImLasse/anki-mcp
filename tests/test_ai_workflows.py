"""Real MCP workflows for vision input, native masks and custom medical note types."""

import asyncio
import base64
import json
from pathlib import Path
import struct
import sys
import zlib
import pytest
from addon.registry import ToolError
from test_transport import running_server, TOKEN


def anatomy_image():
    """A valid small PNG fixture, independent of a GUI or imaging dependency."""

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    pixels = b"".join(b"\0" + bytes([180, 220, 230] * 64) for _ in range(64))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("transport", ["http", "stdio"])
def test_official_client_receives_image_and_creates_native_masks(tmp_path, transport):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.stdio import stdio_client

    raw = anatomy_image()

    async def scenario(session):
        initialized = await session.initialize()
        assert "usage_guide" in initialized.instructions
        guide = await session.call_tool("usage_guide", {"topic": "image_occlusion"})
        assert not guide.isError
        assert "normalized" in json.loads(guide.content[0].text)["guide"]
        stored = await session.call_tool("store_media", {"filename": "anatomy.png", "data_base64": base64.b64encode(raw).decode()})
        filename = json.loads(stored.content[0].text)["filename"]
        viewed = await session.call_tool("get_image", {"filename": filename})
        assert not viewed.isError
        image = next(block for block in viewed.content if block.type == "image")
        assert image.mimeType == "image/png"
        assert base64.b64decode(image.data) == raw
        models = json.loads((await session.call_tool("list_notetypes", {})).content[0].text)
        native = next(model for model in models if model["native_image_occlusion"])
        created = await session.call_tool(
            "create_image_occlusion",
            {
                "deck_id": 1,
                "filename": filename,
                "notetype_id": native["id"],
                "rectangles": [
                    {"ordinal": 1, "left": 0.10, "top": 0.20, "width": 0.20, "height": 0.10},
                    {"ordinal": 1, "left": 0.50, "top": 0.20, "width": 0.20, "height": 0.10},
                    {"ordinal": 2, "left": 0.10, "top": 0.60, "width": 0.20, "height": 0.10},
                ],
                "header": "Benenne die Struktur",
                "back_extra": "Quelle: eigenes Schema",
                "tags": ["Medizin::Anatomie"],
            },
        )
        assert not created.isError
        note = json.loads(created.content[0].text)
        assert len(note["card_ids"]) == 2
        parsed = await session.call_tool("get_image_occlusion", {"note_id": note["id"]})
        shapes = json.loads(parsed.content[0].text)["note"]["occlusions"]
        assert sorted(len(group["shapes"]) for group in shapes) == [1, 2]
        cards = await session.call_tool("get_cards", {"card_ids": note["card_ids"], "render": True})
        assert not cards.isError
        assert all("anatomy.png" in card["question"] for card in json.loads(cards.content[0].text))

    async def connect(server):
        url = f"http://127.0.0.1:{server.server_port}/mcp"
        if transport == "http":
            async with streamablehttp_client(url, headers={"Authorization": "Bearer " + TOKEN}) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await scenario(session)
        else:
            token = tmp_path / "token"
            token.write_text(TOKEN)
            script = Path(__file__).resolve().parents[1] / "addon" / "bridge.py"
            params = StdioServerParameters(command=sys.executable, args=[str(script), "--url", url, "--token-file", str(token)])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await scenario(session)

    with running_server(tmp_path) as server:
        asyncio.run(connect(server))


def test_native_type_clone_with_localized_fields_remains_editable(service):
    native = next(m for m in service.execute("list_notetypes", {}) if m["native_image_occlusion"])
    clone = service.execute("clone_notetype", {"notetype_id": native["id"], "name": "Medizin – Bildverdeckung"})
    names = ["Verdeckung", "Bild", "Überschrift", "Quelle", "Kommentar"]
    for field, name in zip(clone["flds"], names):
        field["name"] = name
    # Rename through the native manager so Anki rewrites field references in templates.
    original = service.model(clone["id"])
    for field, name in zip(original["flds"], names):
        service.col.models.rename_field(original, field, name)
    service.col.models.update_dict(original)
    catalog = next(m for m in service.execute("list_notetypes", {}) if m["id"] == clone["id"])
    assert catalog["fields"] == names
    assert catalog["native_image_occlusion"] is True
    service.execute("store_media", {"filename": "bild.png", "data_base64": base64.b64encode(anatomy_image()).decode()})
    note = service.execute(
        "create_image_occlusion",
        {
            "deck_id": 1,
            "notetype_id": clone["id"],
            "filename": "bild.png",
            "rectangles": [{"ordinal": 1, "left": 0.1, "top": 0.2, "width": 0.2, "height": 0.1}],
            "back_extra": "Eigenes Lehrschema",
        },
    )
    assert note["fields"]["Quelle"] == "Eigenes Lehrschema"
    assert len(note["card_ids"]) == 1
    service.execute("update_image_occlusion", {"note_id": note["id"], "header": "Neue Frage"})
    assert service.col.get_note(note["id"])["Überschrift"] == "Neue Frage"


def test_foreign_type_is_not_classified_by_its_name(service):
    foreign = service.execute(
        "create_notetype",
        {
            "name": "Ankiphil - iOcclusion",
            "fields": ["Bild", "Masken", "Quelle"],
            "templates": [{"name": "Karte", "qfmt": "{{Bild}}", "afmt": "{{Bild}}<hr>{{Masken}}"}],
        },
    )
    row = next(m for m in service.execute("list_notetypes", {}) if m["id"] == foreign["id"])
    assert row["native_image_occlusion"] is False
    service.execute("store_media", {"filename": "bild.png", "data_base64": base64.b64encode(anatomy_image()).decode()})
    before = service.col.note_count()
    with pytest.raises(ToolError, match="native Image Occlusion"):
        service.execute(
            "create_image_occlusion",
            {
                "deck_id": 1,
                "notetype_id": foreign["id"],
                "filename": "bild.png",
                "rectangles": [{"ordinal": 1, "left": 0.1, "top": 0.2, "width": 0.2, "height": 0.1}],
            },
        )
    assert service.col.note_count() == before


def test_create_own_medical_type_with_two_templates_and_sources(service):
    guide = service.execute("usage_guide", {"topic": "notetypes"})["guide"]
    # Execute the documented example, including its fields and template syntax.
    start = guide.index('{"name":"Medizin - Quellenkarten"')
    example, _ = json.JSONDecoder().raw_decode(guide[start:])
    model = service.execute("create_notetype", example)
    note = service.execute(
        "add_notes",
        {
            "notes": [
                {
                    "deck_id": 1,
                    "notetype_id": model["id"],
                    "fields": {
                        "Frage": "Welche Zellen bilden Insulin?",
                        "Antwort": "β-Zellen des Pankreas",
                        "Quelle": "Vom Nutzer angegebene Quelle",
                    },
                    "tags": ["Medizin::Endokrinologie"],
                }
            ]
        },
    )[0]
    assert len(note["card_ids"]) == 2
    rendered = service.execute("get_cards", {"card_ids": note["card_ids"], "render": True})
    assert all("Vom Nutzer angegebene Quelle" in card["answer"] for card in rendered)
    assert "Welche Zellen" in rendered[0]["question"]
    assert "β-Zellen" in rendered[1]["question"]


@pytest.mark.parametrize("topic", ["start", "image_occlusion", "notetypes", "learning", "media", "quality"])
def test_guides_available_in_read_only_mode(service, topic):
    service.read_only = True
    assert service.execute("usage_guide", {"topic": topic})["guide"]


def test_image_view_rejects_unsupported_large_and_external_files(service):
    service.execute("store_media", {"filename": "vector.svg", "data_base64": base64.b64encode(b"<svg></svg>").decode()})
    with pytest.raises(ToolError, match="Expected PNG"):
        service.execute("get_image", {"filename": "vector.svg"})
    path = service.file("huge.png", media=True)
    with path.open("wb") as handle:
        handle.truncate(4 * 1024 * 1024 + 1)
    with pytest.raises(ToolError, match="4 MiB"):
        service.execute("get_image", {"filename": "huge.png"})
    with pytest.raises(ToolError):
        service.execute("get_image", {"filename": "../outside.png"})
