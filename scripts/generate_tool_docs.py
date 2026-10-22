#!/usr/bin/env python3
"""Generate reviewed tool catalog from the exact MCP input schemas."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from addon.api import Service  # noqa: E402,F401
from addon.registry import TOOLS  # noqa: E402


def generate():
    public = [t.public() for t in TOOLS.values()]
    (ROOT / "docs" / "tools.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# MCP-Werkzeuge",
        "",
        f"{len(public)} Werkzeuge. Automatisch aus dem Tool-Register erzeugt.",
        "",
        "Die vollständigen JSON-Eingabeschemas stehen in [tools.json](tools.json). Native Einstellungsfelder lassen sich mit `native_schema` abfragen.",
        "",
        "| Werkzeug | Zugriff | Zweck |",
        "| --- | --- | --- |",
    ]
    for spec in TOOLS.values():
        mode = "Lesen" if not spec.write else "Schreiben"
        if spec.destructive:
            mode += ", `confirm=true`"
        lines.append(f"| `{spec.name}` | {mode} | {spec.description.replace('|', '/')} |")
    (ROOT / "docs" / "tools.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
