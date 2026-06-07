"""Display helpers: glyphs that degrade to ASCII, and the theme name to use.

Color is never the only carrier of meaning here (the HP bar and party balls always
pair their glyph with a number or a count), so honoring ``NO_COLOR`` means swapping
the block and circle glyphs for plain ASCII and using the terminal's own ANSI palette
instead of a designed one. These read the environment on each call so a test (or a
user toggling NO_COLOR) takes effect without a restart.
"""

from __future__ import annotations

import os


def use_ascii() -> bool:
    """True when the user asked for no color (NO_COLOR set), so prefer ASCII glyphs."""
    return bool(os.environ.get("NO_COLOR"))


def hp_glyphs() -> tuple[str, str]:
    """Return the (filled, empty) glyphs for the HP bar."""
    return ("#", "-") if use_ascii() else ("█", "░")


def ball_glyphs() -> tuple[str, str]:
    """Return the (alive, fainted) glyphs for the party balls."""
    return ("o", ".") if use_ascii() else ("●", "○")


def theme_name(theme: str) -> str:
    """Map a 'dark'/'light' preference to a Textual theme (ANSI palette under NO_COLOR)."""
    suffix = "light" if theme == "light" else "dark"
    prefix = "ansi" if use_ascii() else "textual"
    return f"{prefix}-{suffix}"
