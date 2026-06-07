"""Cached sprite art assets and a small loader."""

from __future__ import annotations

from importlib.resources import files


def load_sprite(sprite_key: str, view: str) -> str:
    """Return the cached ANSI art for a sprite. ``view`` is 'front' or 'back'."""
    resource = files("climon.assets").joinpath("sprites", f"{sprite_key}.{view}.ans")
    return resource.read_text(encoding="utf-8")
