"""Unit tests for the display helpers and the status widgets' rendering."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from climon.tui.display import ball_glyphs, hp_glyphs, theme_name, use_ascii
from climon.tui.widgets.hpbar import HPBar
from climon.tui.widgets.partyballs import PartyBalls


def test_theme_name_maps_preference() -> None:
    assert theme_name("dark") == "textual-dark"
    assert theme_name("light") == "textual-light"
    assert theme_name("sunshine") == "textual-dark"


def test_no_color_uses_ascii_glyphs_and_ansi_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert use_ascii() is True
    assert hp_glyphs() == ("#", "-")
    assert ball_glyphs() == ("o", ".")
    assert theme_name("dark") == "ansi-dark"
    assert theme_name("light") == "ansi-light"


def test_color_default_uses_block_glyphs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert use_ascii() is False
    assert hp_glyphs() == ("█", "░")
    assert ball_glyphs() == ("●", "○")


def test_hpbar_ticks_the_number_with_the_fill() -> None:
    # The numeric HP is derived from the fill fraction, so it eases with the bar.
    bar = HPBar(100, 100)
    bar.set_reactive(HPBar.pct, 0.4)
    assert "40/100" in bar.render().plain
    bar.set_reactive(HPBar.pct, 0.1)
    assert "10/100" in bar.render().plain


def test_partyballs_marks_fainted_members(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    plain = PartyBalls([True, False, True]).render().plain
    assert plain.count("●") == 2
    assert plain.count("○") == 1


class _BarApp(App[None]):
    def __init__(self, bar: HPBar) -> None:
        self._bar = bar
        super().__init__()

    def compose(self) -> ComposeResult:
        yield self._bar


async def test_hpbar_instant_update_when_not_animating() -> None:
    bar = HPBar(100, 100)
    async with _BarApp(bar).run_test():
        bar.set_hp(25, 100, animate=False)
        assert abs(bar.pct - 0.25) < 1e-6
        assert "25/100" in bar.render().plain
