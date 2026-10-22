"""Exercise real Qt main-thread dispatch without launching the full Anki UI."""

from concurrent.futures import ThreadPoolExecutor
import importlib
import time
from types import SimpleNamespace
import pytest


def test_qt_profile_lifecycle_and_main_thread(service, tmp_path, monkeypatch):
    pytest.importorskip("aqt")
    from aqt.qt import QCoreApplication

    app = QCoreApplication.instance() or QCoreApplication([])
    from aqt.taskman import TaskManager

    desktop = importlib.import_module("addon.desktop")
    config = {"port": 18766, "enabled": True, "read_only": False, "token": ""}

    class Manager:
        def addonFromModule(self, _module):
            return "anki_mcp"

        def getConfig(self, _id):
            return config.copy()

        def writeConfig(self, _id, value):
            config.update(value)

    ui = SimpleNamespace(
        addonManager=Manager(),
        col=service.col,
        _background_op_count=0,
        state="deckBrowser",
        progress=SimpleNamespace(busy=lambda: False),
        reset=lambda: None,
    )
    ui.weakref = lambda: ui
    ui.taskman = TaskManager(ui)
    monkeypatch.setattr(desktop, "mw", ui)
    # Fail instead of opening a blocking GUI warning on startup errors.
    monkeypatch.setattr(desktop, "showWarning", lambda message: pytest.fail(message))
    runtime = desktop.Runtime()
    runtime.root = tmp_path / "addon"
    runtime.root.mkdir()
    runtime.start()
    assert runtime.server is not None
    assert len(config["token"]) >= 32
    assert (runtime.root / "user_files" / "token").read_text() == config["token"]

    def await_main(future):
        deadline = time.monotonic() + 5
        while not future.done() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.001)
        return future.result(timeout=1)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await_main(executor.submit(runtime.dispatch, "create_deck", {"name": "Qt::Test"}))
            assert service.col.decks.have(result["deck_id"])
            ui._background_op_count = 1
            with pytest.raises(Exception, match="busy"):
                await_main(executor.submit(runtime.dispatch, "create_deck", {"name": "Blocked"}))
            ui._background_op_count = 0
            future = executor.submit(runtime.dispatch, "create_deck", {"name": "Never execute after close"})
            deadline = time.monotonic() + 3
            while not runtime.pending and time.monotonic() < deadline:
                time.sleep(0.001)
            runtime.stop()
            with pytest.raises(Exception):
                await_main(future)
            app.processEvents()
            assert not service.col.decks.id_for_name("Never execute after close")
    finally:
        runtime.stop()
