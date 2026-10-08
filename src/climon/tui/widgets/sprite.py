"""A panel that renders a cached chafa sprite as truecolor terminal art."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from climon.assets import load_sprite


class SpritePanel(Static):
    """Displays one Pokemon's sprite, loaded from its cached .ans file."""

    def __init__(self, sprite_key: str, view: str, *, id: str | None = None) -> None:
        self._sprite_key = sprite_key
        self._view = view
        super().__init__(self._render_art(), id=id)

    def _render_art(self) -> Text:
        return Text.from_ansi(load_sprite(self._sprite_key, self._view).rstrip("\n"))

    def set_pokemon(self, sprite_key: str, view: str) -> None:
        """Swap the displayed sprite (used on switch and forced replacement)."""
        self._sprite_key = sprite_key
        self._view = view
        self.update(self._render_art())

    def flash(self) -> None:
        """Briefly dim the sprite to signal it was hit."""
        self.add_class("hit")
        self.set_timer(0.14, self._unflash)

    def _unflash(self) -> None:
        self.remove_class("hit")
