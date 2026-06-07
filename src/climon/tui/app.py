"""The climon Textual application."""

from __future__ import annotations

import random
from typing import ClassVar

from textual.app import App
from textual.binding import BindingType

from climon.ai.opponents import GreedyAI
from climon.config import get_settings
from climon.engine.data import full_team
from climon.engine.models import BattleState
from climon.transport.base import BattleSession
from climon.transport.local import LocalSession
from climon.tui.display import theme_name
from climon.tui.screens.battle import BattleScreen
from climon.tui.screens.online_lobby import OnlineLobby
from climon.tui.screens.pick_lead import PickLeadScreen


class ClimonApp(App[None]):
    """The root app: pick a lead and battle the computer, or go online."""

    CSS_PATH = "styles.tcss"
    TITLE = "climon"
    BINDINGS: ClassVar[list[BindingType]] = [("ctrl+q", "quit", "Quit")]

    def __init__(self, session: BattleSession | None = None, *, online: bool = False) -> None:
        super().__init__()
        self._session = session
        self._online = online

    def on_mount(self) -> None:
        self.theme = theme_name(get_settings().theme)
        if self._session is not None:
            self.push_screen(BattleScreen(self._session))
        elif self._online:
            self.push_screen(OnlineLobby())
        else:
            self.push_screen(PickLeadScreen())


def demo_session() -> LocalSession:
    """A ready-to-play battle (Bulbasaur lead vs a Charmander lead), used by tests."""
    state = BattleState(teams=(full_team(lead="Bulbasaur"), full_team(lead="Charmander")))
    return LocalSession(state, GreedyAI(), random.Random())
