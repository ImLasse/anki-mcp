import pytest
from addon.registry import ToolError


def test_search_edit_tags_and_render(service, note):
    nid, cid = note["id"], note["card_ids"][0]
    assert service.execute("search", {"query": "tag:Medizin::Anatomie", "kind": "notes"})["items"] == [nid]
    service.execute("edit_tags", {"note_ids": [nid], "tags": ["Examen::M1"], "action": "add"})
    assert "Examen::M1" in service.execute("get_notes", {"note_ids": [nid]})[0]["tags"]
    service.execute("update_notes", {"updates": [{"note_id": nid, "fields": {"Back": "<b>Nervus phrenicus</b>"}}]})
    card = service.execute("get_cards", {"card_ids": [cid], "render": True})[0]
    assert "Nervus phrenicus" in card["answer"]
    service.execute("rename_tag", {"old": "Examen", "new": "Prüfung"})
    assert "Prüfung::M1" in service.execute("list_tags", {})["tags"]
    service.execute("remove_tag", {"tag": "Prüfung", "confirm": True})
    service.execute("delete_notes", {"note_ids": [nid], "confirm": True})
    assert service.col.note_count() == 0
    service.execute("undo", {"confirm": True})
    assert service.col.note_count() == 1


def test_batch_validation_before_write(service, basic, note):
    with pytest.raises(ToolError):
        service.execute(
            "add_notes",
            {
                "notes": [
                    {"deck_id": 1, "notetype_id": basic, "fields": {"Front": "Valid"}},
                    {"deck_id": 1, "notetype_id": basic, "fields": {"Unknown": "Invalid"}},
                ]
            },
        )
    assert service.col.note_count() == 1
    with pytest.raises(ToolError):
        service.execute(
            "update_notes",
            {"updates": [{"note_id": note["id"], "fields": {"Front": "Changed"}}, {"note_id": 123, "fields": {"Unknown": "Invalid"}}]},
        )
    assert service.col.get_note(note["id"])["Front"].startswith("Welcher")


def test_duplicate_rejection(service, basic, note):
    data = {"deck_id": 1, "notetype_id": basic, "fields": note["fields"]}
    with pytest.raises(ToolError, match="Duplicate"):
        service.execute("add_notes", {"notes": [data]})
    data["allow_duplicate"] = True
    service.execute("add_notes", {"notes": [data]})
    assert service.col.note_count() == 2


def test_cloze_generation(service):
    mid = service.col.models.by_name("Cloze")["id"]
    result = service.execute(
        "add_notes",
        {"notes": [{"deck_id": 1, "notetype_id": mid, "fields": {"Text": "{{c1::Insulin}} wird in {{c2::β-Zellen}} gebildet."}}]},
    )
    assert len(result[0]["card_ids"]) == 2


def test_schedule_and_learning_data(service, note):
    cid = note["card_ids"][0]
    for action, queue in [("suspend", -1), ("unsuspend", 0), ("bury", -3), ("unbury", 0)]:
        service.execute("schedule_cards", {"card_ids": [cid], "action": action, "confirm": True})
        assert service.col.get_card(cid).queue == queue
    service.execute("schedule_cards", {"card_ids": [cid], "action": "flag", "flag": 3, "confirm": True})
    assert service.col.get_card(cid).user_flag() == 3
    service.execute("schedule_cards", {"card_ids": [cid], "action": "set_due", "days": "4", "confirm": True})
    assert service.col.get_card(cid).due == service.col.sched.today + 4
    assert service.execute("learning_overview", {"query": "tag:Medizin::Anatomie"})["counts"]["review"] == 1
    assert service.execute("learning_statistics", {"query": "", "days": 30})
    assert service.execute("card_statistics", {"card_ids": [cid]})[0]["statistics"]
    assert isinstance(service.execute("review_history", {"card_id": cid})["items"], list)
    service.execute("schedule_cards", {"card_ids": [cid], "action": "forget", "confirm": True, "reset_counts": True})
    service.execute("schedule_cards", {"card_ids": [cid], "action": "reposition", "start": 50, "confirm": True})
    assert service.col.get_card(cid).due == 50
    other = service.execute("create_deck", {"name": "Neu"})["deck_id"]
    service.execute("schedule_cards", {"card_ids": [cid], "action": "move", "deck_id": other, "confirm": True})
    assert service.col.get_card(cid).did == other


def test_real_review_writes_history(service, note):
    cid = note["card_ids"][0]
    service.execute("select_deck", {"deck_id": 1})
    assert service.execute("review_queue", {})["queue"]["cards"][0]["card"]["id"] == str(cid)
    service.execute("answer_card", {"card_id": cid, "rating": 3, "milliseconds_taken": 3500, "confirm": True})
    assert service.col.get_card(cid).reps == 1
    assert len(service.execute("review_history", {"card_id": cid})["items"]) == 1


def test_filtered_deck(service, note):
    cid = note["card_ids"][0]
    service.execute("schedule_cards", {"card_ids": [cid], "action": "set_due", "days": "0", "confirm": True})
    data = service.execute("filtered_deck", {"action": "create", "name": "Prüfung", "query": "tag:Medizin::Anatomie"})
    did = data["deck_id"]
    assert service.col.get_card(cid).did == did
    service.execute("filtered_deck", {"action": "empty", "deck_id": did})
    assert service.col.get_card(cid).did == 1
    service.execute("filtered_deck", {"action": "update", "deck_id": did, "query": "is:due"})
    service.execute("filtered_deck", {"action": "rebuild", "deck_id": did})


def test_convert_note_type(service, note):
    reverse = service.col.models.by_name("Basic (and reversed card)")["id"]
    service.execute(
        "change_notetype", {"note_ids": [note["id"]], "notetype_id": reverse, "field_map": [0, 1], "template_map": [0, -1], "confirm": True}
    )
    n = service.col.get_note(note["id"])
    assert n.mid == reverse
    assert len(n.card_ids()) == 2


def test_duplicate_search_and_native_replace(service, basic, note):
    service.execute("add_notes", {"notes": [{"deck_id": 1, "notetype_id": basic, "fields": note["fields"], "allow_duplicate": True}]})
    duplicates = service.execute("find_duplicates", {"field_name": "Front"})
    assert duplicates["total"] == 1
    service.execute(
        "find_replace", {"note_ids": [note["id"]], "search": "phrenicus", "replacement": "PHRENICUS", "field_name": "Back", "confirm": True}
    )
    assert "PHRENICUS" in service.col.get_note(note["id"])["Back"]


def test_custom_study_and_fsrs_preview(service, note):
    before = service.col.get_card(note["card_ids"][0]).reps
    defaults = service.execute("custom_study_defaults", {"deck_id": 1})
    assert "available_new" in defaults
    service.execute("custom_study", {"request": {"deck_id": 1, "new_limit_delta": 10}, "confirm": True})
    params = service.execute("fsrs_parameters", {"deck_id": 1, "action": "compute"})
    assert params["fsrs_items"] == 0
    assert service.col.get_card(note["card_ids"][0]).reps == before
    with pytest.raises(ToolError, match="history"):
        service.execute("fsrs_parameters", {"deck_id": 1, "action": "evaluate"})
