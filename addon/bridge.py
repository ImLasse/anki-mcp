#!/usr/bin/env python3
"""Dependency-free MCP stdio -> authenticated Anki Streamable HTTP bridge."""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def local_opener():
    # Keep private collection traffic local, including when a proxy is configured.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def connection_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 401:
            return "Anmeldung fehlgeschlagen (401). Token und Client-Konfiguration aktualisieren."
        if exc.code == 403:
            return "Verbindung abgewiesen (403). Lokale Adresse und Origin prüfen."
        return f"Anki antwortet mit HTTP {exc.code}. Adresse und Port prüfen."
    return "Anki ist nicht erreichbar oder antwortet nicht korrekt. Profil, Port und Konfiguration prüfen."


def check_connection(url, token):
    """Read-only MCP smoke check. Called off the GUI thread or with --check."""
    opener = local_opener()

    def call(request_id, method, params=None):
        request = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            request["params"] = params
        req = urllib.request.Request(
            url,
            data=json.dumps(request).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with opener.open(req, timeout=15) as response:
            data = json.load(response)
        if data.get("error") or not isinstance(data.get("result"), dict):
            raise ValueError("Invalid MCP response")
        result = data["result"]
        if result.get("isError"):
            raise ValueError("Anki profile is not ready")
        return result

    initialized = call(
        1,
        "initialize",
        {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "anki-mcp-setup-check", "version": "0.3.0"}},
    )
    tools = call(2, "tools/list")
    collection = call(3, "tools/call", {"name": "collection_info", "arguments": {}})
    info = json.loads(collection["content"][0]["text"])
    return {
        "ok": True,
        "server": initialized["serverInfo"]["name"],
        "protocol": initialized["protocolVersion"],
        "tool_count": len(tools["tools"]),
        "cards": info["cards"],
        "notes": info["notes"],
        "read_only": info["read_only"],
    }


def main():
    # MCP frames are UTF-8 even when Windows pipes use another locale encoding.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766/mcp")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--check", action="store_true", help="Run a read-only connection check and exit")
    args = parser.parse_args()
    parsed = urlsplit(args.url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost")
        or parsed.path != "/mcp"
        or parsed.username
        or parsed.query
        or parsed.fragment
    ):
        parser.error("--url must point to the local http://127.0.0.1:PORT/mcp endpoint")
    token = args.token_file.read_text(encoding="utf-8").strip() if args.token_file else os.environ.get("ANKI_MCP_TOKEN", "")
    if len(token) < 32:
        parser.error("Set ANKI_MCP_TOKEN or --token-file to the token shown in Anki's Tools menu")

    if args.check:
        try:
            report = check_connection(args.url, token)
        except (ValueError, OSError, urllib.error.URLError) as exc:
            print(json.dumps({"ok": False, "message": connection_error(exc)}, ensure_ascii=False), flush=True)
            return 1
        print(json.dumps(report, ensure_ascii=False), flush=True)
        return 0
    opener = local_opener()
    for line in sys.stdin.buffer:
        request = None
        try:
            if len(line) > 32 * 1024 * 1024:
                raise ValueError("Request exceeds 32 MiB")
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("JSON-RPC object required")
            req = urllib.request.Request(
                args.url,
                data=line,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with opener.open(req, timeout=300) as response:
                raw = response.read()
            if raw:
                print(raw.decode("utf-8"), flush=True)
        except (ValueError, OSError, urllib.error.URLError) as exc:
            # Never log headers, tokens or note contents.
            print(
                f"Anki connection failed ({type(exc).__name__}); verify Anki is running and token/port match.", file=sys.stderr, flush=True
            )
            if isinstance(request, dict) and "id" in request:
                print(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "error": {
                                "code": -32000,
                                "message": "Anki connection failed. Operation outcome may be unknown; inspect before retrying.",
                            },
                        }
                    ),
                    flush=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
