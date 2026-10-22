"""Anki loads this module after aqt.mw exists; core can also run headless."""

import sys

if getattr(sys.modules.get("aqt"), "mw", None) is not None:
    from .desktop import install

    install()
