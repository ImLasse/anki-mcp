"""Real collection workflows: reviewed edits, revision tracking and honest planning."""

from datetime import date, timedelta
import json
import pytest
from addon.api import Service
from addon.registry import ToolError
from test_collection import current_options


def note_plan(service, nid, value="N. phrenicus"):
    return service.execute(
        "plan_changes", {"calls": [{"tool": "update_notes", "arguments": {"updates": [{"note_id": nid, "fields": {"Back": value}}]}}]}
    )


def test_persistent_review_apply_journal_and_native_undo(service, note):
    before = service.col.get_note(note["id"])["Back"]
    plan = note_plan(service, note["id"])
    assert service.col.get_note(note["id"])["Back"] == before
    assert any(x["before"] == before and x["after"] == "N. phrenicus" for x in plan["previews"][0]["changes"])
    restarted = Service(service.col, service.files_dir)
    restarted.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    assert service.col.get_note(note["id"])["Back"] == "N. phrenicus"
    history = restarted.execute("change_history", {})
    entry = next(x for x in history["items"] if x["tool"] == "apply_change_plan")
    details = restarted.execute("change_history", {"entry_id": entry["id"]})["items"][0]
    assert details["before"]["operations"][0]["notes"][str(note["id"])]["fields"]["Back"] == before
    assert details["after"]["operations"][0]["notes"][str(note["id"])]["fields"]["Back"] == "N. phrenicus"
    with pytest.raises(ToolError, match="unused"):
        restarted.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    restarted.execute("undo", {"confirm": True})
    assert service.col.get_note(note["id"])["Back"] == before


def test_stale_plan_and_missing_confirmation_do_not_mutate(service, note):
    plan = note_plan(service, note["id"])
    with pytest.raises(ToolError, match="confirm"):
        service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": False})
    native = service.col.get_note(note["id"])
    native["Back"] = "Manual edit"
    service.col.update_note(native)
    with pytest.raises(ToolError, match="changed after preview"):
        service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    assert service.col.get_note(note["id"])["Back"] == "Manual edit"


def test_expired_plan_and_duplicate_targets(service, note):
    plan = note_plan(service, note["id"])
    data = service.store.get("plan", plan["id"])
    data["expires"] = "2000-01-01T00:00:00+00:00"
    service.store.put("plan", data, plan["id"])
    with pytest.raises(ToolError, match="expired"):
        service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    with pytest.raises(ToolError, match="same target"):
        service.execute("plan_changes", {"calls": plan["calls"] * 2})


def test_card_plan_suspends_and_preserves_history(service, note):
    cid = note["card_ids"][0]
    service.execute("schedule_cards", {"card_ids": [cid], "action": "set_due", "days": "3", "confirm": True})
    old = service.col.get_card(cid)
    plan = service.execute(
        "plan_changes", {"calls": [{"tool": "schedule_cards", "arguments": {"card_ids": [cid], "action": "suspend", "confirm": True}}]}
    )
    assert service.col.get_card(cid).queue != -1
    service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    after = service.col.get_card(cid)
    assert after.queue == -1 and after.ivl == old.ivl and after.reps == old.reps
    service.execute("undo", {"confirm": True})
    assert service.col.get_card(cid).queue == old.queue


@pytest.mark.parametrize("action,tags", [("remove", ["Medizin"]), ("remove", ["Medizin::Anatomie"]), ("add", ["MEDIZIN::ANATOMIE", "Neu"])])
def test_tag_preview_matches_native_hierarchical_semantics(service, note, action, tags):
    plan = service.execute(
        "plan_changes", {"calls": [{"tool": "edit_tags", "arguments": {"note_ids": [note["id"]], "action": action, "tags": tags}}]}
    )
    changes = plan["previews"][0]["changes"]
    predicted = next((x["after"] for x in changes if x["path"].endswith(".tags")), note["tags"])
    service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    assert sorted(t.casefold() for t in service.col.get_note(note["id"]).tags) == sorted(t.casefold() for t in predicted)


def test_shared_preset_plan_shows_scope_and_invalidates(service):
    other = service.execute("create_deck", {"name": "Histologie"})["deck_id"]
    plan = service.execute(
        "plan_changes", {"calls": [{"tool": "set_deck_options", "arguments": {"deck_id": 1, "patch": {"new_per_day": 17}, "shared": True}}]}
    )
    assert {1, other} <= set(next(x["after"] for x in plan["previews"][0]["changes"] if x["path"] == "affected_deck_ids"))
    assert current_options(service, 1)["config"]["new_per_day"] != 17
    service.execute("apply_change_plan", {"plan_id": plan["id"], "confirm": True})
    assert current_options(service, other)["config"]["new_per_day"] == 17


def test_journal_survives_actual_collection_close_and_isolates_profiles(service, note, tmp_path):
    from anki.collection import Collection

    path = service.col.path
    files = service.files_dir
    plan = note_plan(service, note["id"])
    old_path = service.store.path
    service.col.close()
    service.col = Collection(path)
    restarted = Service(service.col, files)
    assert restarted.store.path == old_path
    assert restarted.store.get("plan", plan["id"])["status"] == "draft"
    assert restarted.execute("change_history", {})["total"] >= 2
    other = Collection(str(tmp_path / "other.anki2"))
    try:
        assert Service(other, files).execute("change_history", {})["total"] == 0
    finally:
        other.close()


def test_post_commit_journal_failure_does_not_encourage_duplicate_write(service, monkeypatch, capsys):
    store = service.store

    def fail(*args):
        raise OSError("secret error text must not escape")

    monkeypatch.setattr(store, "finish", fail)
    result = service.execute("create_deck", {"name": "Created once"})
    assert result["created"] and "journal_warning" in result
    assert service.deck(result["deck_id"])["name"] == "Created once"
    assert store.history()["items"][0]["status"] == "pending"
    assert "secret error text" not in capsys.readouterr().err


def test_revisioned_sources_and_portable_metadata(service, note):
    src = service.execute(
        "create_source",
        {"source": {"title": "Test source <script>alert(1)</script>", "url": "https://example.org/medical", "edition": "1"}},
    )
    service.execute("link_source", {"source_id": src["id"], "note_ids": [note["id"]], "citation_field": "Back", "locator": "S. 12"})
    field = service.col.get_note(note["id"])["Back"]
    assert "&lt;script&gt;" in field and "<script>" not in field
    assert not service.execute("source_notes", {"source_id": src["id"]})["items"][0]["needs_review"]
    service.execute("update_source", {"source_id": src["id"], "source": {"title": "Corrected source", "edition": "2"}})
    assert service.col.get_note(note["id"])["Back"] == field
    service.execute("link_source", {"source_id": src["id"], "note_ids": [note["id"]]})
    assert service.execute("source_notes", {"source_id": src["id"], "needs_review_only": True})["total"] == 1
    service.execute("acknowledge_source_review", {"source_id": src["id"], "note_ids": [note["id"]], "confirm": True})
    exported = service.execute("export_workspace", {})
    service.store.delete("source", src["id"])
    assert service.execute("import_workspace", {"data": exported, "confirm": True})["sources"] == 1
    assert service.execute("source_notes", {"source_id": src["id"], "needs_review_only": True})["total"] == 0
    assert "journal" not in exported and "plans" not in exported


def test_source_import_validates_everything_before_commit(service, note):
    src = service.execute("create_source", {"source": {"title": "Original"}})
    exported = service.execute("export_workspace", {})
    exported["sources"][0]["citation"]["title"] = "Changed"
    exported["links"] = [{"id": "bad"}]
    with pytest.raises(ToolError):
        service.execute("import_workspace", {"data": exported, "confirm": True})
    assert service.store.get("source", src["id"])["citation"]["title"] == "Original"
    with pytest.raises(ToolError):
        service.execute("create_source", {"source": {"title": "x", "url": "javascript:alert(1)"}})
    service.execute("link_source", {"source_id": src["id"], "note_ids": [note["id"]]})
    service.execute("delete_notes", {"note_ids": [note["id"]], "confirm": True})
    assert service.execute("source_notes", {"source_id": src["id"]})["items"][0]["missing_note"]


def test_exam_budget_forecast_excludes_suspended_and_reports_shortfall(service, basic):
    notes = service.execute(
        "add_notes",
        {"notes": [{"deck_id": 1, "notetype_id": basic, "fields": {"Front": f"Nerv {i}", "Back": "Medizin"}} for i in range(6)]},
    )
    cids = [n["card_ids"][0] for n in notes]
    service.execute("schedule_cards", {"card_ids": cids[:2], "action": "set_due", "days": "0", "confirm": True})
    service.execute("schedule_cards", {"card_ids": [cids[2]], "action": "suspend", "confirm": True})
    old = service.col.undo_status().undo
    request = {
        "exam_date": (date.today() + timedelta(days=2)).isoformat(),
        "daily_minutes": 1,
        "new_card_seconds": 120,
        "review_card_seconds": 60,
        "topics": [{"name": "All", "query": ""}],
    }
    report = service.execute("exam_plan", request)
    assert report["new_cards"] == 3 and report["unallocated_new_cards"] == 3
    assert report["days"][0]["scheduled_reviews"] == 2 and report["days"][0]["review_overload_minutes"] == 1
    assert not report["feasible_under_assumptions"] and len(report["days"]) == 2
    assert service.col.undo_status().undo == old
    service.execute("save_exam_plan", {"name": "Exam", "request": request})
    assert service.execute("saved_exam_plans", {})[0]["name"] == "Exam"


def test_exam_weekday_budget_and_future_allocation(service, note):
    start = date.today() + timedelta(days=1)
    weekly = [0] * 7
    weekly[start.weekday()] = 10
    request = {
        "exam_date": (start + timedelta(days=2)).isoformat(),
        "start_date": start.isoformat(),
        "daily_minutes": 1,
        "weekly_minutes": weekly,
    }
    report = service.execute("exam_plan", request)
    assert report["days"][0]["new_cards"] == 1 and report["days"][1]["new_cards"] == 0
    assert report["feasible_under_assumptions"]
    with pytest.raises(ToolError):
        service.execute("exam_plan", {"exam_date": "not a date", "daily_minutes": 10})


def test_similarity_returns_candidates_without_mutation(service, basic):
    texts = [
        "Der Nervus phrenicus innerviert das Zwerchfell",
        "Der Nervus phrenicus innerviert NICHT das Zwerchfell",
        "Ein völlig anderes Thema: Gerinnungsfaktoren und Antikoagulanzien",
    ]
    notes = service.execute(
        "add_notes", {"notes": [{"deck_id": 1, "notetype_id": basic, "fields": {"Front": t, "Back": "Quelle prüfen"}} for t in texts]}
    )
    undo = service.col.undo_status().undo
    pairs = service.execute("similar_notes", {"fields": ["Front"], "min_score": 0.5})
    assert any(set(x["note_ids"]) == {notes[0]["id"], notes[1]["id"]} for x in pairs["items"])
    assert service.col.undo_status().undo == undo and service.col.note_count() == 3
    assert "not semantic" in pairs["method"]
    assert service.execute("similar_notes", {"max_notes": 2})["truncated"]


def test_workspace_read_only_blocks_local_writes(service, note):
    service.read_only = True
    for tool, args in [
        ("create_source", {"source": {"title": "x"}}),
        ("plan_changes", {"calls": [{"tool": "edit_tags", "arguments": {"note_ids": [note["id"]], "tags": ["x"], "action": "add"}}]}),
    ]:
        with pytest.raises(ToolError, match="read_only"):
            service.execute(tool, args)
    assert service.execute("similar_notes", {})["scanned"] == 1
    assert json.dumps(service.execute("export_workspace", {}))
