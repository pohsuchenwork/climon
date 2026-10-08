"""A name, level, HP bar, and party-ball summary for one side of the battle."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from climon.tui.widgets.hpbar import HPBar
from climon.tui.widgets.partyballs import PartyBalls


class InfoBox(Vertical):
    """The labeled status box shown for the player and the opponent."""

    def __init__(
        self,
        name: str,
        level: int,
        current_hp: int,
        max_hp: int,
        alive: list[bool],
        *,
        id: str | None = None,
    ) -> None:
        self._poke_name = name
        self._level = level
        self._current_hp = current_hp
        self._max_hp = max_hp
        self._alive = alive
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Label(f"{self._poke_name}  [dim]Lv{self._level}[/]", classes="info-name")
        yield HPBar(self._current_hp, self._max_hp)
        yield PartyBalls(self._alive, id=None)
