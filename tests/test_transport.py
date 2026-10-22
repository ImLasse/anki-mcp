import asyncio
from concurrent.futures import Future
from contextlib import contextmanager
import json
from pathlib import Path
import queue
import sys
import threading
import urllib.error
import urllib.request
import pytest
from addon.protocol import Protocol
from addon.server import Server

TOKEN = "x" * 43


@contextmanager
def running_server(tmp_path):
    """Own the real collection on one thread; mimic Qt main-thread dispatch."""
    tasks = queue.Queue()
    ready = Future()

    def collection_thread():
        from anki.collection import Collection
        from addon.api import Service

        col = Collection(str(tmp_path / "transport.anki2"))
        service = Service(col, tmp_path / "files")
        ready.set_result(True)
        try:
            while (item := tasks.get()) is not None:
                name, arguments, future = item
                try:
                    future.set_result(service.execute(name, arguments))
                except Exception as exc:
                    future.set_exception(exc)
        finally:
            col.close()

    worker = threading.Thread(target=collection_thread, daemon=True)
    worker.start()
    ready.result(10)

    def execute(name, arguments):
        future = Future()
        tasks.put((name, arguments, future))
        return future.result(10)

    server = Server(0, TOKEN, Protocol(execute))
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
        tasks.put(None)
        worker.join()


def post(server, data, **headers):
    defaults = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    defaults.update(headers)
    req = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/mcp", data=data, headers=defaults)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=10)


def test_http_auth_origin_host_and_errors(tmp_path):
    with running_server(tmp_path) as server:
        ping = b'{"jsonrpc":"2.0","id":1,"method":"ping"}'
        for headers, status in [
            ({"Authorization": ""}, 401),
            ({"Origin": "https://evil.example"}, 403),
            ({"Host": "evil.example"}, 403),
            ({"Content-Type": "text/plain"}, 415),
        ]:
            with pytest.raises(urllib.error.HTTPError) as exc:
                post(server, ping, **headers)
            assert exc.value.code == status
        with post(server, ping) as res:
            assert json.load(res)["result"] == {}
        with pytest.raises(urllib.error.HTTPError) as exc:
            post(server, b"not-json")
        assert exc.value.code == 400
        with post(server, b'{"jsonrpc":"2.0","method":"notifications/initialized"}') as res:
            assert res.status == 202
        with post(server, b'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search","arguments":{"query":true}}}') as res:
            assert json.load(res)["result"]["isError"] is True


def test_invalid_rpc_and_no_notification_mutations():
    called = []
    p = Protocol(lambda n, a: called.append(n))
    assert p.handle([])["error"]["code"] == -32600
    assert p.handle({"jsonrpc": "2.0", "id": 3, "method": "missing"})["error"]["code"] == -32601
    assert p.handle({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "create_deck", "arguments": {"name": "Never"}}}) is None
    assert not called
    error = p.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "not-real"}})
    assert error["error"]["code"] == -32602


def test_official_sdk_over_streamable_http(tmp_path):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async def scenario(url):
        async with streamablehttp_client(url, headers={"Authorization": "Bearer " + TOKEN}) as (read, write, _):
            async with ClientSession(read, write) as session:
                result = await session.initialize()
                assert result.serverInfo.name == "anki-mcp"
                tools = await session.list_tools()
                assert len(tools.tools) >= 50
                result = await session.call_tool("create_deck", {"name": "Medizin::MCP"})
                assert not result.isError
                decks = await session.call_tool("list_decks", {})
                assert "Medizin::MCP" in decks.content[0].text

    with running_server(tmp_path) as server:
        asyncio.run(scenario(f"http://127.0.0.1:{server.server_port}/mcp"))


def test_official_sdk_over_stdio_bridge(tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    script = Path(__file__).resolve().parents[1] / "scripts" / "anki_mcp_bridge.py"
    token = tmp_path / "token"
    token.write_text(TOKEN)

    async def scenario(url):
        params = StdioServerParameters(command=sys.executable, args=[str(script), "--url", url, "--token-file", str(token)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("collection_info", {})
                assert not result.isError
                assert json.loads(result.content[0].text)["cards"] == 0

    with running_server(tmp_path) as server:
        asyncio.run(scenario(f"http://127.0.0.1:{server.server_port}/mcp"))
