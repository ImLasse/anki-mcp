"""Portable client configuration helpers; no Anki imports or shell execution."""

import json
import os
from pathlib import Path
import platform
import shutil


def python_candidates():
    system = platform.system()
    paths = []
    if system == "Darwin":
        paths.extend(
            [
                Path("/opt/homebrew/bin/python3"),
                Path("/usr/local/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/Current/bin/python3"),
            ]
        )
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            paths.extend(sorted((Path(local) / "Programs" / "Python").glob("Python*/python.exe"), reverse=True))
    for command in ("python3", "python"):
        found = shutil.which(command)
        if found:
            path = Path(found)
            if system == "Darwin" and str(path) == "/usr/bin/python3":
                continue
            if system == "Windows" and "windowsapps" in str(path).casefold():
                continue
            paths.append(path)
    return list(dict.fromkeys(str(p) for p in paths if p.is_file()))


def client_configuration(kind, root, port, token, python_executable=""):
    if kind == "stdio":
        return {
            "mcpServers": {
                "anki": {
                    "command": python_executable or "/ABSOLUTER/PFAD/ZU/python3",
                    "args": [
                        str(root / "bridge.py"),
                        "--url",
                        f"http://127.0.0.1:{port}/mcp",
                        "--token-file",
                        str(root / "user_files" / "token"),
                    ],
                }
            }
        }
    if kind != "http":
        raise ValueError("Unknown connection type")
    return {"mcpServers": {"anki": {"url": f"http://127.0.0.1:{port}/mcp", "headers": {"Authorization": "Bearer " + token}}}}


def configuration_text(*args, **kwargs):
    return json.dumps(client_configuration(*args, **kwargs), ensure_ascii=False, indent=2)


def codex_configuration(root, port, python_executable):
    config = client_configuration("stdio", root, port, "", python_executable)["mcpServers"]["anki"]
    # JSON string/array syntax is also valid for these TOML basic strings/arrays.
    return (
        "[mcp_servers.anki]\ncommand = "
        + json.dumps(config["command"], ensure_ascii=False)
        + "\nargs = "
        + json.dumps(config["args"], ensure_ascii=False)
        + "\nstartup_timeout_sec = 20\ntool_timeout_sec = 300\n"
    )


def tunnel_configuration(port, token, tunnel_id):
    """Native tunnel-client YAML. API key stays in the operator's environment."""

    def quote(value):
        return json.dumps(value, ensure_ascii=False)

    return (
        "# Lokal als anki-tunnel.yaml speichern; enthält deinen Anki-Zugangstoken.\n"
        "config_version: 1\ncontrol_plane:\n"
        "  base_url: https://api.openai.com\n"
        "  tunnel_id: " + quote(tunnel_id or "DEINE_TUNNEL_ID") + "\n"
        "  api_key: env:CONTROL_PLANE_API_KEY\n"
        "health:\n  listen_addr: 127.0.0.1:0\n"
        "mcp:\n  server_urls:\n    - channel: main\n"
        "      url: " + quote(f"http://127.0.0.1:{port}/mcp") + "\n"
        "  extra_headers:\n    Authorization: " + quote("Bearer " + token) + "\n"
        "  discovery_extra_headers:\n    Authorization: " + quote("Bearer " + token) + "\n"
    )
