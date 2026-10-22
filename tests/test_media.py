import base64
import pytest
from addon.registry import ToolError

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5XsAAAAASUVORK5CYII="


def test_media_roundtrip_collision_trash(service, note):
    original = service.execute("store_media", {"filename": "diagram.png", "data_base64": PNG})
    assert original["filename"] == "diagram.png"
    stored = service.execute("read_media", {"filename": "diagram.png", "length": 10})
    assert base64.b64decode(stored["data_base64"]) == base64.b64decode(PNG)[:10]
    assert stored["next_offset"] == 10
    other = service.execute("store_media", {"filename": "diagram.png", "data_base64": base64.b64encode(b"other").decode()})
    assert other["filename"] != "diagram.png"
    assert service.execute("list_media", {})["total"] == 2
    service.execute("update_notes", {"updates": [{"note_id": note["id"], "fields": {"Back": original["image_html"] + "[sound:test.mp3]"}}]})
    report = service.execute("check_media", {})
    assert "test.mp3" in report["missing"]
    service.execute("trash_media", {"filenames": ["diagram.png"], "confirm": True})
    service.execute("restore_media_trash", {})
    assert service.execute("read_media", {"filename": "diagram.png"})["data_base64"] == PNG


@pytest.mark.parametrize("filename", ["../secret", "/etc/passwd", "..", ".", "dir\\x", "C:foo", "a\x00b"])
def test_no_arbitrary_media_paths(service, filename):
    with pytest.raises(ToolError):
        service.execute("read_media", {"filename": filename})


def test_symlink_rejected(service, tmp_path):
    path = service.file("link", media=True)
    path.symlink_to(tmp_path / "secret")
    with pytest.raises(ToolError):
        service.execute("read_media", {"filename": "link"})


def test_native_occlusion_roundtrip(service):
    service.execute("store_media", {"filename": "anatomy.png", "data_base64": PNG})
    result = service.execute(
        "create_image_occlusion",
        {
            "deck_id": 1,
            "filename": "anatomy.png",
            "rectangles": [
                {"ordinal": 1, "left": 0.1, "top": 0.2, "width": 0.3, "height": 0.4},
                {"ordinal": 2, "left": 0.5, "top": 0.5, "width": 0.2, "height": 0.2},
            ],
            "tags": ["Anatomie"],
            "header": "Beschrifte",
        },
    )
    assert len(result["card_ids"]) == 2
    parsed = service.execute("get_image_occlusion", {"note_id": result["id"]})
    assert "rect" in str(parsed)
    assert "image_data" not in str(parsed)
    service.execute(
        "update_image_occlusion",
        {
            "note_id": result["id"],
            "rectangles": [{"ordinal": 1, "left": 0.1, "top": 0.1, "width": 0.2, "height": 0.2}],
            "back_extra": "Quelle: Lehrbuch",
        },
    )
    empty = service.execute("empty_cards", {})
    assert empty["notes"]
    stale = next(c.id for c in service.col.get_note(result["id"]).cards() if c.ord == 1)
    service.execute("delete_cards", {"card_ids": [stale], "confirm": True})
    assert len(service.col.get_note(result["id"]).card_ids()) == 1


def test_package_export_import_and_transfer(service, note):
    result = service.execute("export_package", {"filename": "medizin.apkg", "deck_id": 1})
    assert result["size"] > 0
    chunk = service.execute("transfer_file", {"action": "download", "filename": "medizin.apkg"})
    service.execute("transfer_file", {"action": "upload", "filename": "copy.apkg", "data_base64": chunk["data_base64"]})
    with pytest.raises(ToolError):
        service.execute("transfer_file", {"action": "upload", "filename": "copy.apkg", "data_base64": chunk["data_base64"]})
    service.execute("import_package", {"filename": "copy.apkg", "confirm": True})
    assert service.col.note_count() == 1
    service.execute("transfer_file", {"action": "delete", "filename": "copy.apkg", "confirm": True})
    assert len(service.execute("transfer_file", {"action": "list"})) == 1
    assert service.execute("create_backup", {})["includes_media"] is False


def test_deck_export_excludes_other_decks(service, note, basic, tmp_path):
    from anki.collection import Collection

    other = service.execute("create_deck", {"name": "Other"})["deck_id"]
    service.execute("add_notes", {"notes": [{"deck_id": other, "notetype_id": basic, "fields": {"Front": "Should not export"}}]})
    service.execute("export_package", {"filename": "only-one.apkg", "deck_id": 1})
    from anki.import_export_pb2 import ImportAnkiPackageRequest

    col = Collection(str(tmp_path / "fresh.anki2"))
    try:
        col.import_anki_package(ImportAnkiPackageRequest(package_path=str(service.file("only-one.apkg"))))
        assert col.note_count() == 1
    finally:
        col.close()
