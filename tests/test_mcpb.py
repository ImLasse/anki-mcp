"""Install the exact Claude bundle and exercise its transport with the official SDK."""

import asyncio
import base64
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from scripts.build import build_mcpb
from test_ai_workflows import anatomy_image
from test_transport import running_server, TOKEN


def test_installed_claude_bundle_real_images_utf8_and_workflows(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node 20+ required for MCPB integration")
    installed = tmp_path / "Anki Claude extension with spaces"
    with zipfile.ZipFile(build_mcpb()) as archive:
        archive.extractall(installed)
        assert "server/index.js" in archive.namelist()
        assert not any("token" == Path(x).name for x in archive.namelist())
    manifest = json.loads((installed / "manifest.json").read_text())
    assert manifest["compatibility"]["platforms"] == ["darwin", "win32", "linux"]
    tokenfile = tmp_path / "token with spaces"
    tokenfile.write_text(TOKEN)

    async def scenario(port):
        params = StdioServerParameters(
            command=node, args=[str(installed / "server/index.js"), "--port", str(port), "--token-file", str(tokenfile)]
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert "plan_changes" in initialized.instructions
                result = await session.call_tool("create_deck", {"name": "Medizin::β-Zellen 🫀"})
                assert not result.isError
                decks = await session.call_tool("list_decks", {})
                assert "β-Zellen 🫀" in decks.content[0].text
                stored = await session.call_tool(
                    "store_media", {"filename": "anatomy.png", "data_base64": base64.b64encode(anatomy_image()).decode()}
                )
                assert not stored.isError
                image = await session.call_tool("get_image", {"filename": "anatomy.png"})
                assert not image.isError
                block = next(x for x in image.content if x.type == "image")
                assert base64.b64decode(block.data) == anatomy_image()
                source = await session.call_tool("create_source", {"source": {"title": "Anatomie β", "edition": "1"}})
                assert not source.isError
                history = await session.call_tool("change_history", {})
                assert "create_source" in history.content[0].text

    with running_server(tmp_path) as server:
        asyncio.run(scenario(server.server_port))


def test_mcpb_invalid_credentials_do_not_leak(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required")
    token = tmp_path / "token"
    token.write_text("private unsafe token")
    script = Path(__file__).resolve().parents[1] / "clients" / "claude" / "server" / "index.js"
    result = subprocess.run([node, str(script), "--token-file", str(token)], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and not result.stdout
    assert "private unsafe token" not in result.stderr
