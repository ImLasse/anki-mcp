#!/usr/bin/env python3
"""Reproducible, credential-free .ankiaddon packaging."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    output = ROOT / "dist" / "anki-mcp-0.2.0.ankiaddon"
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


if __name__ == "__main__":
    build()
