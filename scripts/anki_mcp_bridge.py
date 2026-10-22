#!/usr/bin/env python3
"""Repository entry point; the standalone bridge is bundled in addon/bridge.py."""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "addon" / "bridge.py"), run_name="__main__")
