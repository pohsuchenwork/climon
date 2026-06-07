"""A row of balls showing how many team members are still standing."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from climon.tui.display import ball_glyphs


class PartyBalls(Static):
    """One filled ball per live member, one hollow ball per fainted member."""

    def __init__(self, alive: list[bool], *, id: str | None = None) -> None:
        self._alive = alive
        super().__init__(id=id)

    def set_alive(self, alive: list[bool]) -> None:
        self._alive = alive
        self.refresh()

    def render(self) -> Text:
        live, dead = ball_glyphs()
        text = Text()
        for member_alive in self._alive:
            glyph = f"{live} " if member_alive else f"{dead} "
            text.append(glyph, style="green" if member_alive else "grey37")
        return text
