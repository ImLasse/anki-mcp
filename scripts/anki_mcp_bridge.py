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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766/mcp")
    parser.add_argument("--token-file", type=Path)
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

    # Disable inherited proxies for local private collection traffic and reject redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
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
