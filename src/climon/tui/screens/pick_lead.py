"""Draft your team of three from the roster before battling the computer."""

from __future__ import annotations

import random

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Label

from climon.ai.opponents import GreedyAI
from climon.engine.data import ROSTER, TEAM_SIZE, make_team, random_team
from climon.engine.models import BattleState, Species
from climon.transport.local import LocalSession
from climon.tui.screens.battle import BattleScreen


def _types(species: Species) -> str:
    return " / ".join(part.value for part in species.types)


class PickLeadScreen(Screen[None]):
    """Draft three Pokemon (your lead first), then battle the computer."""

    def __init__(self) -> None:
        self._picks: list[str] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="pick-root"):
            yield Label("c l i m o n", id="pick-logo")
            yield Label("Draft your team: pick 3 (your lead first).", id="pick-title")
            for index, species in enumerate(ROSTER):
                yield Label(
                    f"  [b]{index + 1:>2}[/]  {species.name}  [dim]({_types(species)})[/]",
                    classes="pick-option",
                )
            yield Label("", id="pick-team")
            yield Input(placeholder="type a number, a name, or 'back' to undo", id="pick-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#pick-input", Input).focus()

    @on(Input.Submitted, "#pick-input")
    def _on_pick(self, event: Input.Submitted) -> None:
        text = event.value.strip().lower()
        event.input.value = ""
        if text in ("quit", "exit"):
            self.app.exit()
            return
        if text in ("back", "undo", "cancel"):
            self._undo()
            return
        if len(self._picks) >= TEAM_SIZE:
            return  # already have a full team
        species = self._match(text)
        if species is None:
            self._title("Pick a number 1-12 or a name:")
            return
        if species.name in self._picks:
            self._title(f"{species.name} is already on your team. Pick another:")
            return
        self._picks.append(species.name)
        if len(self._picks) >= TEAM_SIZE:
            self._start_battle()
        else:
            self._update_team()

    def _undo(self) -> None:
        if self._picks:
            removed = self._picks.pop()
            self._title(f"Removed {removed}. Draft your team: pick 3 (your lead first).")
            self._update_team()
        else:
            self._title("Draft your team: pick 3 (your lead first).")

    def _match(self, text: str) -> Species | None:
        if text.isdigit():
            index = int(text) - 1
            return ROSTER[index] if 0 <= index < len(ROSTER) else None
        for species in ROSTER:
            if text and species.name.lower().startswith(text):
                return species
        return None

    def _title(self, text: str) -> None:
        self.query_one("#pick-title", Label).update(text)

    def _update_team(self) -> None:
        remaining = TEAM_SIZE - len(self._picks)
        chosen = ", ".join(self._picks)
        self.query_one("#pick-team", Label).update(
            f"[b]Team:[/] {chosen}  [dim](pick {remaining} more)[/]"
        )

    def _start_battle(self) -> None:
        rng = random.Random()
        state = BattleState(teams=(make_team(self._picks), random_team(rng, TEAM_SIZE)))
        self.app.switch_screen(BattleScreen(LocalSession(state, GreedyAI(), rng)))
