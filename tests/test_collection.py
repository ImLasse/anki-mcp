import pytest
from addon.registry import ToolError, TOOLS
from jsonschema import Draft202012Validator


def test_all_schemas():
    assert len(TOOLS) >= 50
    for tool in TOOLS.values():
        Draft202012Validator.check_schema(tool.schema)
        assert tool.public()["annotations"]["readOnlyHint"] == (not tool.write)


def test_deck_crud_and_undo(service):
    deck = service.execute("create_deck", {"name": "Medizin::Anatomie"})
    did = deck["deck_id"]
    assert service.execute("create_deck", {"name": "Medizin::Anatomie"})["created"] is False
    service.execute("rename_deck", {"deck_id": did, "name": "Medizin::Histologie"})
    service.execute("update_deck", {"deck_id": did, "patch": {"desc": "Prüfungsstoff"}})
    assert service.execute("get_deck", {"deck_id": did})["desc"] == "Prüfungsstoff"
    with pytest.raises(ToolError):
        service.execute("delete_decks", {"deck_ids": [did], "confirm": False})
    service.execute("delete_decks", {"deck_ids": [did], "confirm": True})
    assert not service.col.decks.have(did)
    service.execute("undo", {"confirm": True})
    assert service.col.decks.have(did)
    service.execute("redo", {"confirm": True})
    assert not service.col.decks.have(did)


def current_options(service, did):
    data = service.execute("get_deck_options", {"deck_id": did})
    cid = data["current_deck"]["config_id"]
    return next(x["config"] for x in data["all_config"] if x["config"]["id"] == cid)


def test_full_native_options_clone_and_shared(service):
    other = service.execute("create_deck", {"name": "Medizin"})["deck_id"]
    original = current_options(service, other)
    service.execute(
        "set_deck_options",
        {
            "deck_id": 1,
            "patch": {"new_per_day": 42, "reviews_per_day": 321, "desired_retention": 0.93, "learn_steps": [2, 15], "bury_new": True},
            "global_fsrs": True,
        },
    )
    updated = current_options(service, 1)
    assert updated["config"]["new_per_day"] == 42
    assert updated["config"]["desired_retention"] == pytest.approx(0.93)
    assert current_options(service, other) == original
    assert service.execute("get_deck_options", {"deck_id": 1})["fsrs"] is True
    service.execute("assign_deck_preset", {"deck_id": other, "preset_id": int(updated["id"])})
    service.execute("set_deck_options", {"deck_id": 1, "patch": {"new_per_day": 77}, "shared": True})
    assert current_options(service, other)["config"]["new_per_day"] == 77
    with pytest.raises(ToolError):
        service.execute("set_deck_options", {"deck_id": 1, "patch": {"invented": 3}})


def test_preferences_preserve_other_settings(service):
    before = service.execute("get_preferences", {})
    service.execute("set_preferences", {"patch": {"scheduling": {"learn_ahead_secs": 600}}})
    after = service.execute("get_preferences", {})
    assert after["scheduling"]["learn_ahead_secs"] == 600
    assert after["backups"] == before["backups"]


def test_notetype_creation_clone_modify(service):
    model = service.execute(
        "create_notetype",
        {
            "name": "Medizin",
            "fields": ["Frage", "Antwort", "Quelle"],
            "templates": [{"name": "Karte", "qfmt": "{{Frage}}", "afmt": "{{FrontSide}}<hr>{{Antwort}}<br>{{Quelle}}"}],
            "css": ".card {font-size: 22px}",
        },
    )
    service.execute("add_notes", {"notes": [{"deck_id": 1, "notetype_id": model["id"], "fields": {"Frage": "Test", "Antwort": "Antwort"}}]})
    clone = service.execute("clone_notetype", {"notetype_id": model["id"], "name": "Kopie"})
    assert clone["id"] != model["id"]
    model["flds"][2]["name"] = "Referenz"
    service.execute(
        "update_notetype", {"notetype_id": model["id"], "patch": {"flds": model["flds"], "css": ".card{color:blue}"}, "confirm": True}
    )
    assert service.execute("get_notetype", {"notetype_id": model["id"]})["flds"][2]["name"] == "Referenz"
    service.execute("delete_notetype", {"notetype_id": clone["id"], "confirm": True})


def test_read_only_rejects_every_write(service):
    service.read_only = True
    with pytest.raises(ToolError, match="read_only"):
        service.execute("create_deck", {"name": "blocked"})
    assert service.execute("collection_info", {})["read_only"] is True


def test_daily_deck_limits_preserved(service):
    service.execute("set_deck_options", {"deck_id": 1, "patch": {}, "limits": {"new": 12, "review": 80}})
    result = service.execute("get_deck_options", {"deck_id": 1})
    assert result["current_deck"]["limits"]["new"] == 12
    service.execute("set_deck_options", {"deck_id": 1, "patch": {"new_per_day": 25}})
    assert service.execute("get_deck_options", {"deck_id": 1})["current_deck"]["limits"]["review"] == 80


@pytest.mark.parametrize("name", ["deck_config", "deck_limits", "preferences", "custom_study", "import_options"])
def test_native_schemas(service, name):
    schema = service.execute("native_schema", {"name": name})
    assert schema["fields"]
    assert schema["message"].startswith("anki.")
