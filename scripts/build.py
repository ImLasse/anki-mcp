#!/usr/bin/env python3
"""Reproducible, credential-free .ankiaddon packaging."""

from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "addon" / "manifest.json").read_text(encoding="utf-8"))["version"]


def build():
    output = ROOT / "dist" / f"anki-mcp-{VERSION}.ankiaddon"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "addon").iterdir()):
            if path.is_file() and path.suffix in (".py", ".json", ".md"):
                info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("LICENSE.txt", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, (ROOT / "LICENSE").read_bytes())
    print(output)
    return output


def build_mcpb():
    output = ROOT / "dist" / f"anki-mcp-claude-{VERSION}.mcpb"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "clients" / "claude").rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(ROOT / "clients" / "claude").as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("LICENSE.txt", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, (ROOT / "LICENSE").read_bytes())
    print(output)
    return output


if __name__ == "__main__":
    build()
    build_mcpb()
