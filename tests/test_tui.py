"""Structural and snapshot tests for the screens."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from textual.widgets import Input

from climon.config import get_settings
from climon.tui.app import ClimonApp, demo_session
from climon.tui.screens.battle import BattleScreen
from climon.tui.screens.online_lobby import OnlineLobby
from climon.tui.screens.pick_lead import PickLeadScreen
from climon.tui.screens.resize_guard import ResizeGuard
from climon.tui.widgets.infobox import InfoBox
from climon.tui.widgets.partyballs import PartyBalls
from climon.tui.widgets.sprite import SpritePanel


async def test_battle_screen_mounts() -> None:
    app = ClimonApp(demo_session())
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        assert len(app.screen.query(SpritePanel)) == 2
        assert len(app.screen.query(InfoBox)) == 2
        assert len(app.screen.query(".command-cell")) == 4
        assert app.screen.query_one("#message-log") is not None


async def test_boots_straight_to_pick_lead() -> None:
    app = ClimonApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PickLeadScreen)


async def test_pick_lead_starts_battle() -> None:
    app = ClimonApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PickLeadScreen)
        app.screen.query_one("#pick-input", Input).focus()
        # Draft three Pokemon; the third pick starts the battle.
        await pilot.press("1", "enter", "2", "enter", "3", "enter")
        await pilot.pause()
        assert isinstance(app.screen, BattleScreen)


async def test_online_lobby_mounts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIMON_SERVER", "ws://localhost:1")
    get_settings.cache_clear()
    try:
        app = ClimonApp(online=True)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, OnlineLobby)
            assert app.screen.query_one("#lobby-input", Input) is not None
    finally:
        get_settings.cache_clear()


async def test_pick_lead_undo_and_draft_three() -> None:
    app = ClimonApp()
    async with app.run_test(size=(100, 44)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, PickLeadScreen)
        screen.query_one("#pick-input", Input).focus()
        await pilot.press("1", "enter", "2", "enter")
        assert screen._picks == ["Bulbasaur", "Charmander"]
        await pilot.press(*"back", "enter")  # undo the last pick
        assert screen._picks == ["Bulbasaur"]
        await pilot.press("2", "enter", "3", "enter")  # back up to three -> starts
        await pilot.pause()
        assert isinstance(app.screen, BattleScreen)


async def test_resize_guard_appears_when_terminal_too_small() -> None:
    app = ClimonApp(demo_session())
    async with app.run_test(size=(70, 20)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, ResizeGuard)


async def test_no_resize_guard_at_full_size() -> None:
    app = ClimonApp(demo_session())
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, BattleScreen)


async def test_battle_uses_ascii_glyphs_under_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    app = ClimonApp(demo_session())
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        plain = app.screen.query(PartyBalls).first().render().plain
        assert "o" in plain
        assert "●" not in plain


def test_battle_screen_snapshot(snap_compare: Callable[..., bool]) -> None:
    assert snap_compare(ClimonApp(demo_session()), terminal_size=(100, 40))


def test_pick_lead_snapshot(snap_compare: Callable[..., bool]) -> None:
    assert snap_compare(ClimonApp(), terminal_size=(100, 44))
