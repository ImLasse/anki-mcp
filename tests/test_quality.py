from addon.registry import ToolError
import pytest
from test_ai_workflows import anatomy_image
import base64


def test_preview_does_not_save_and_reports_existing_duplicates(service, basic, note):
    service.read_only = True
    before = service.col.note_count(), service.col.card_count(), service.col.undo_status().undo
    preview = service.execute("preview_notes", {"notes": [{"deck_id": 1, "notetype_id": basic, "fields": note["fields"]}]})
    assert preview["saved"] is False
    assert preview["rendered_cards"] == 1
    assert "phrenicus" in preview["notes"][0]["cards"][0]["answer"]
    assert any("Duplicate" in item for item in preview["notes"][0]["warnings"])
    assert (service.col.note_count(), service.col.card_count(), service.col.undo_status().undo) == before


def test_preview_cloze_uses_sparse_native_ordinals(service):
    mid = service.col.models.by_name("Cloze")["id"]
    result = service.execute(
        "preview_notes",
        {"notes": [{"deck_id": 1, "notetype_id": mid, "fields": {"Text": "{{c1::Insulin}} wird in {{c3::β-Zellen}} gebildet."}}]},
    )
    assert [card["ordinal"] for card in result["notes"][0]["cards"]] == [0, 2]
    assert service.col.note_count() == service.col.card_count() == 0


def test_preview_renders_custom_target_deck(service):
    did = service.execute("create_deck", {"name": "Medizin::Anatomie"})["deck_id"]
    model = service.execute(
        "create_notetype",
        {
            "name": "Deckanzeige",
            "fields": ["Frage"],
            "templates": [{"name": "Karte", "qfmt": "{{Deck}}: {{Frage}}", "afmt": "{{FrontSide}}"}],
        },
    )
    result = service.execute("preview_notes", {"notes": [{"deck_id": did, "notetype_id": model["id"], "fields": {"Frage": "Nerven?"}}]})
    assert result["notes"][0]["deck_name"] == "Medizin::Anatomie"
    assert "(Deck)" in result["notes"][0]["cards"][0]["question"]
    assert "placeholders" in result["renderer"]
    assert service.col.note_count() == 0


def test_audit_missing_sources_media_and_optional_fields(service, basic):
    service.execute("store_media", {"filename": "present.png", "data_base64": base64.b64encode(anatomy_image()).decode()})
    notes = service.execute(
        "add_notes",
        {
            "notes": [
                {"deck_id": 1, "notetype_id": basic, "fields": {"Front": "Nerven?", "Back": "<p>&nbsp;<br></p>"}, "tags": ["audit"]},
                {
                    "deck_id": 1,
                    "notetype_id": basic,
                    "fields": {"Front": "Gefäße?", "Back": '<img src="missing.png">[sound:missing.mp3]'},
                    "tags": ["audit"],
                },
                {"deck_id": 1, "notetype_id": basic, "fields": {"Front": "Bild?", "Back": '<img src="present.png">'}, "tags": ["audit"]},
            ]
        },
    )
    service.read_only = True
    report = service.execute("audit_notes", {"query": "tag:audit", "required_fields": ["Back", "Quelle"]})
    by_id = {item["note_id"]: item for item in report["items"]}
    assert by_id[notes[0]["id"]]["empty_required_fields"] == ["Back"]
    assert {x["filename"] for x in by_id[notes[1]["id"]]["missing_media"]} == {"missing.png", "missing.mp3"}
    assert not by_id[notes[2]["id"]]["missing_media"]
    assert not by_id[notes[2]["id"]]["empty_required_fields"]
    assert by_id[notes[2]["id"]]["unknown_required_fields"] == ["Quelle"]
    assert "source reliability" in report["scope"]
    assert service.col.note_count() == 3


def test_audit_pages_scope_and_remote_media(service, basic):
    for front in ["A", "B", "C"]:
        service.execute(
            "add_notes",
            {
                "notes": [
                    {
                        "deck_id": 1,
                        "notetype_id": basic,
                        "fields": {"Front": front, "Back": '<img src="https://example.com/image.png">'},
                        "tags": ["scope"],
                    }
                ]
            },
        )
    first = service.execute("audit_notes", {"query": "tag:scope", "limit": 2})
    second = service.execute("audit_notes", {"query": "tag:scope", "limit": 2, "offset": first["next_offset"]})
    assert first["total"] == 3 and first["scanned"] == 2 and second["scanned"] == 1
    assert not first["notes_with_issues"]
    assert not any(item["missing_media"] for item in first["items"])
    assert second["next_offset"] is None
    assert set(x["note_id"] for x in first["items"]).isdisjoint(x["note_id"] for x in second["items"])


def test_preview_rejects_unknown_fields_without_adding_notes(service, basic):
    with pytest.raises(ToolError, match="Unknown field"):
        service.execute("preview_notes", {"notes": [{"deck_id": 1, "notetype_id": basic, "fields": {"Wrong": "test"}}]})
    assert service.col.note_count() == 0


def test_preview_warns_about_duplicates_in_new_batch(service, basic):
    proposed = {"deck_id": 1, "notetype_id": basic, "fields": {"Front": "Prüfungsfrage?", "Back": "Antwort"}}
    result = service.execute("preview_notes", {"notes": [proposed, proposed]})
    assert any("batch" in warning for warning in result["notes"][1]["warnings"])
    assert service.col.note_count() == 0
