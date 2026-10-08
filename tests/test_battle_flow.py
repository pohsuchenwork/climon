"""Interaction tests: typed commands, submenus, back, and run-confirm."""

from __future__ import annotations

import random

from textual.widgets import Input, RichLog

from climon.ai.opponents import RandomAI
from climon.engine.actions import Action
from climon.engine.data import full_team
from climon.engine.events import Event
from climon.engine.models import BattleState
from climon.transport.local import LocalSession
from climon.tui.app import ClimonApp
from climon.tui.screens.battle import BattleScreen


class _ClosableSession:
    """Wraps a LocalSession and records whether close() was called."""

    def __init__(self, inner: LocalSession) -> None:
        self._inner = inner
        self.closed = False

    @property
    def state(self) -> BattleState:
        return self._inner.state

    @property
    def player_slot(self) -> int:
        return self._inner.player_slot

    @property
    def winner(self) -> int | None:
        return self._inner.winner

    async def submit(self, action: Action) -> list[Event]:
        return await self._inner.submit(action)

    async def replace(self, index: int) -> list[Event]:
        return await self._inner.replace(index)

    async def close(self) -> None:
        self.closed = True


def _app() -> tuple[ClimonApp, LocalSession]:
    BattleScreen.MESSAGE_DELAY = 0.0
    state = BattleState(teams=(full_team(lead="Bulbasaur"), full_team(lead="Charmander")))
    session = LocalSession(state, RandomAI(), random.Random(3))
    return ClimonApp(session), session


async def test_typing_a_move_resolves_a_turn() -> None:
    app, session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        app.screen.query_one("#command-input", Input).focus()
        await pilot.press(*"tackle", "enter")
        await pilot.pause()
        await pilot.pause()
        assert session.state.turn == 1


async def test_unknown_command_does_not_advance() -> None:
    app, session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        app.screen.query_one("#command-input", Input).focus()
        await pilot.press(*"xyzzy", "enter")
        await pilot.pause()
        assert session.state.turn == 0


async def test_fight_submenu_then_select_resolves_turn() -> None:
    app, session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, BattleScreen)
        screen.query_one("#command-input", Input).focus()
        await pilot.press(*"fight", "enter")
        await pilot.pause()
        assert screen._mode == "fight"
        await pilot.press("2", "enter")
        await pilot.pause()
        await pilot.pause()
        assert session.state.turn == 1
        assert screen._mode == "main"


async def test_back_cancels_a_submenu() -> None:
    app, session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, BattleScreen)
        screen.query_one("#command-input", Input).focus()
        await pilot.press(*"fight", "enter")
        await pilot.pause()
        assert screen._mode == "fight"
        await pilot.press(*"back", "enter")
        await pilot.pause()
        assert screen._mode == "main"
        assert session.state.turn == 0


async def test_run_confirm_then_yes_flees() -> None:
    app, _session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, BattleScreen)
        screen.query_one("#command-input", Input).focus()
        await pilot.press(*"run", "enter")
        await pilot.pause()
        assert screen._mode == "run_confirm"
        await pilot.press(*"yes", "enter")
        await pilot.pause()
        await pilot.pause()
        assert screen._over


async def test_bag_potion_heals_then_resolves_the_turn() -> None:
    BattleScreen.MESSAGE_DELAY = 0.0
    state = BattleState(teams=(full_team(lead="Bulbasaur"), full_team(lead="Charmander")))
    active = state.team(0).active
    active.current_hp = active.max_hp - 50
    session = LocalSession(state, RandomAI(), random.Random(3))
    app = ClimonApp(session)
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, BattleScreen)
        screen.query_one("#command-input", Input).focus()
        await pilot.press(*"bag", "enter")
        await pilot.pause()
        assert screen._mode == "bag"
        await pilot.press("1", "enter")  # Potion
        await pilot.pause()
        assert screen._mode == "bag_target"
        await pilot.press("1", "enter")  # use it on the active Pokemon
        await pilot.pause()
        await pilot.pause()
        assert session.state.turn == 1
        assert session.state.team(0).bag["Potion"] == 1  # one Potion spent


async def test_quitting_closes_the_session() -> None:
    BattleScreen.MESSAGE_DELAY = 0.0
    state = BattleState(teams=(full_team(lead="Bulbasaur"), full_team(lead="Charmander")))
    session = _ClosableSession(LocalSession(state, RandomAI(), random.Random(0)))
    app = ClimonApp(session)
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        app.screen.query_one("#command-input", Input).focus()
        await pilot.press(*"quit", "enter")
        await pilot.pause()
        assert session.closed  # leaving tells the session (so an online opponent is freed)


async def test_type_command_shows_matchup_without_advancing() -> None:
    BattleScreen.MESSAGE_DELAY = 0.0
    app, session = _app()
    async with app.run_test(size=(110, 30)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, BattleScreen)
        screen.query_one("#command-input", Input).focus()
        log = screen.query_one("#message-log", RichLog)
        before = len(log.lines)
        await pilot.press(*"type", "enter")
        await pilot.pause()
        assert session.state.turn == 0  # scouting does not use a turn
        assert len(log.lines) > before  # it printed the matchup
        assert screen._mode == "main"
