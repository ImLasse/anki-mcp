"""User-facing setup tests, including installed files and paths with spaces."""

import asyncio
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import time
import tomllib
from types import SimpleNamespace
import zipfile
import pytest
from addon.bridge import check_connection
from addon.connection import client_configuration, configuration_text, codex_configuration
from test_transport import running_server, TOKEN


@pytest.mark.parametrize(
    "root,python_path",
    [
        (Path("/Users/Lasse/Library/Application Support/Anki2/addons21/anki_mcp"), "/opt/homebrew/bin/python3"),
        (Path("/Users/Lasse/Library/Application Support/Anki2/addons21/anki_mcp"), "/usr/local/bin/python3"),
        (
            PureWindowsPath(r"C:\Users\Dein Name\AppData\Roaming\Anki2\addons21\anki_mcp"),
            r"C:\Users\Dein Name\AppData\Local\Programs\Python\Python312\python.exe",
        ),
    ],
)
def test_copyable_client_paths_do_not_need_shell_escaping(root, python_path):
    cfg = json.loads(configuration_text("stdio", root, 8767, TOKEN, python_path))["mcpServers"]["anki"]
    assert cfg["command"] == python_path
    assert cfg["args"][0] == str(root / "bridge.py")
    assert cfg["args"][-1] == str(root / "user_files" / "token")
    assert cfg["args"][2] == "http://127.0.0.1:8767/mcp"
    assert not any(arg.startswith('"') for arg in cfg["args"])
    assert TOKEN not in json.dumps(cfg)
    codex = tomllib.loads(codex_configuration(root, 8767, python_path))["mcp_servers"]["anki"]
    assert codex["command"] == cfg["command"]
    assert codex["args"] == cfg["args"]


def test_packaged_bridge_runs_without_repository_or_anki_imports(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("setup_build", root / "scripts" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    installed = tmp_path / "Library" / "Application Support" / "Anki2" / "addons21" / "Anki MCP"
    with zipfile.ZipFile(module.build()) as archive:
        archive.extractall(installed)
    (installed / "user_files").mkdir()
    (installed / "user_files" / "token").write_text(TOKEN)
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def scenario(config):
        params = StdioServerParameters(command=config["command"], args=config["args"], cwd=str(tmp_path), env={"PYTHONIOENCODING": "ascii"})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("list_decks", {})
                assert not result.isError
                assert "Default" in result.content[0].text
                created = await session.call_tool("create_deck", {"name": "Medizin::β-Zellen 🫀"})
                assert not created.isError
                listed = await session.call_tool("list_decks", {})
                assert "β-Zellen 🫀" in listed.content[0].text

    with running_server(tmp_path) as server:
        config = client_configuration("stdio", installed, server.server_port, TOKEN, sys.executable)["mcpServers"]["anki"]
        asyncio.run(scenario(config))
        checked = subprocess.run(
            [config["command"], *config["args"], "--check"], cwd=tmp_path, capture_output=True, text=True, timeout=15, check=True
        )
        report = json.loads(checked.stdout)
        assert report["ok"] is True
        assert report["cards"] == report["notes"] == 0
        assert report["tool_count"] >= 61
        assert TOKEN not in checked.stdout + checked.stderr


def test_setup_check_rejects_wrong_token_without_exposing_it(tmp_path):
    with running_server(tmp_path) as server:
        url = f"http://127.0.0.1:{server.server_port}/mcp"
        import urllib.error

        with pytest.raises(urllib.error.HTTPError) as exc:
            check_connection(url, "wrong-token")
        assert exc.value.code == 401
        assert TOKEN not in str(exc.value)


def test_setup_dialog_connects_to_anki_and_preserves_read_only_state(qt_app, tmp_path, monkeypatch):
    from aqt.taskman import TaskManager
    from aqt.qt import QApplication
    from addon import setup_dialog

    with running_server(tmp_path) as server:
        root = Path(__file__).resolve().parents[1] / "addon"
        runtime = SimpleNamespace(server=server, config={"token": TOKEN, "read_only": False}, root=root, error=None, generation=1)
        ui = SimpleNamespace()
        ui.weakref = lambda: ui
        ui.taskman = TaskManager(ui)
        monkeypatch.setattr(setup_dialog, "mw", ui)
        dialog = setup_dialog.SetupDialog(runtime)
        dialog.show()
        qt_app.processEvents()
        try:
            guide = dialog.help_browser.toPlainText()
            assert "Claude Desktop auf Windows" in guide
            assert "Claude Desktop auf macOS" in guide
            assert "ChatGPT" in guide
            assert TOKEN not in guide
            assert "Bildverdeckung erstellen" in dialog.usage_browser.toPlainText()
            assert "Vorschau vor dem Speichern" in dialog.usage_browser.toPlainText()
            dialog.sections.setCurrentIndex(1)
            assert dialog.help_browser.textCursor().selectedText() == "Claude Desktop auf Windows"
            dialog.tabs.setCurrentIndex(1)
            dialog.python_path.setText(sys.executable)
            dialog.copy.click()
            cfg = json.loads(QApplication.clipboard().text())["mcpServers"]["anki"]
            assert cfg["command"] == sys.executable
            dialog.method.setCurrentIndex(1)
            dialog.copy.click()
            http_cfg = json.loads(QApplication.clipboard().text())["mcpServers"]["anki"]
            assert http_cfg["headers"]["Authorization"] == "Bearer " + TOKEN
            dialog.method.setCurrentIndex(2)
            dialog.copy.click()
            codex = tomllib.loads(QApplication.clipboard().text())["mcp_servers"]["anki"]
            assert codex["command"] == sys.executable
            dialog.method.setCurrentIndex(3)
            assert not dialog.copy.isEnabled()
            dialog.tunnel_id.setText("tunnel_" + "a" * 32)
            dialog.copy.click()
            yaml = QApplication.clipboard().text()
            assert "env:CONTROL_PLANE_API_KEY" in yaml
            assert "tunnel_" + "a" * 32 in yaml
            assert "Bearer " + TOKEN in yaml
            dialog.check.click()
            deadline = time.monotonic() + 10
            while not dialog.check.isEnabled() and time.monotonic() < deadline:
                qt_app.processEvents()
                time.sleep(0.001)
            assert "Verbindung erfolgreich" in dialog.result.text()
            assert "0 Notizen und 0 Karten" in dialog.result.text()
            assert TOKEN not in dialog.result.text()
        finally:
            dialog.close()
            QApplication.clipboard().clear()


def test_help_available_when_server_is_stopped(qt_app):
    from addon.setup_dialog import SetupDialog

    runtime = SimpleNamespace(
        server=None, config={}, root=Path(__file__).resolve().parents[1] / "addon", error="Profil öffnen.", generation=1
    )
    dialog = SetupDialog(runtime)
    assert not dialog.copy.isEnabled()
    assert not dialog.check.isEnabled()
    assert "Anki MCP einrichten" in dialog.help_browser.toPlainText()
    dialog.close()
