"""Qt main-thread dispatch, profile lifecycle and connection dialog."""

import secrets
import threading
from concurrent.futures import Future, TimeoutError
from pathlib import Path
from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showWarning
from .api import Service
from .protocol import Protocol
from .registry import ToolError
from .server import Server


class Runtime:
    def __init__(self):
        self.server = None
        self.generation = 0
        self.lock = threading.Lock()
        self.pending = set()
        self.error = None
        self.config = {}
        self.root = Path(__file__).resolve().parent
        self.addon_id = mw.addonManager.addonFromModule(__name__)

    def stop(self, *_args):
        with self.lock:
            self.generation += 1
            for future in self.pending:
                future.cancel()
            self.pending.clear()
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def start(self, *_args):
        self.stop()
        self.error = None
        config = mw.addonManager.getConfig(self.addon_id) or {}
        if not config.get("enabled", True):
            return
        if not isinstance(config.get("token"), str) or len(config["token"]) < 32:
            config["token"] = secrets.token_urlsafe(32)
            mw.addonManager.writeConfig(self.addon_id, config)
        try:
            port = config.get("port", 8766)
            if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
                raise ValueError("Port must be an integer between 1024 and 65535")
            user_files = self.root / "user_files"
            user_files.mkdir(mode=0o700, exist_ok=True)
            token_path = user_files / "token"
            token_path.touch(mode=0o600, exist_ok=True)
            token_path.chmod(0o600)
            token_path.write_text(config["token"], encoding="utf-8")
            self.config = config
            self.server = Server(port, config["token"], Protocol(self.dispatch))
            threading.Thread(target=self.server.serve_forever, name="Anki MCP", daemon=True).start()
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            showWarning("Anki MCP konnte nicht gestartet werden. Prüfe Port und Konfiguration.\n" + self.error)

    def dispatch(self, name, arguments):
        future = Future()
        with self.lock:
            generation = self.generation
            self.pending.add(future)

        def run():
            if not future.set_running_or_notify_cancel():
                return
            try:
                if generation != self.generation or not mw.col:
                    raise ToolError("Profile was closed; reconnect to the active profile")
                if getattr(mw, "_background_op_count", 0):
                    raise ToolError("Anki is busy with a background operation; retry after it completes")
                if getattr(mw.progress, "busy", lambda: False)():
                    raise ToolError("Anki is busy; retry when its current operation completes")
                if name == "answer_card" and mw.state == "review":
                    raise ToolError("Leave the GUI reviewer before submitting MCP answers")
                service = Service(mw.col, self.root / "user_files" / "transfers", read_only=self.config.get("read_only", False), ui=mw)
                future.set_result(service.execute(name, arguments))
            except Exception as exc:
                future.set_exception(exc)

        mw.taskman.run_on_main(run)
        try:
            try:
                return future.result(timeout=30)
            except TimeoutError:
                if future.cancel():
                    raise ToolError("Anki did not accept the operation within 30s; nothing was executed")
                # Once started, do not report a false timeout for an operation that may commit.
                return future.result()
        finally:
            with self.lock:
                self.pending.discard(future)

    def dialog(self, *_args, start_tab=0):
        from .setup_dialog import SetupDialog

        dialog = SetupDialog(self, mw, start_tab=start_tab)
        dialog.exec()

    def connection_dialog(self, *_args):
        self.dialog(start_tab=1)


_runtime = None


def install():
    global _runtime
    if _runtime is not None:
        return
    _runtime = Runtime()
    gui_hooks.profile_did_open.append(_runtime.start)
    gui_hooks.profile_will_close.append(_runtime.stop)
    help_action = QAction("Anki MCP – Einrichtung && Hilfe", mw)
    help_action.triggered.connect(_runtime.dialog)
    mw.form.menuTools.addAction(help_action)
    _runtime.help_action = help_action
    action = QAction("Anki MCP – Verbindung", mw)
    action.triggered.connect(_runtime.connection_dialog)
    mw.form.menuTools.addAction(action)
    _runtime.action = action
