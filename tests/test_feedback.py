"""The end-of-match and pre-battle feedback lines: every outcome has a fitting message."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from climon.protocol import messages as wire
from climon.tui.screens.battle import match_end_text
from climon.tui.screens.online_lobby import OnlineLobby


@pytest.mark.parametrize(
    ("reason", "winner", "me", "fled", "needle"),
    [
        ("ko", 0, 0, False, "You win!"),
        ("ko", 1, 0, False, "You lose"),
        ("ko", -1, 0, False, "draw"),
        ("opponent_left", 0, 0, False, "opponent left"),
        ("opponent_left", 0, 0, False, "You win!"),
        ("timeout", 0, 0, False, "ran out of time"),
        ("timeout", 1, 0, False, "You lose"),
        ("connection_lost", -1, 0, False, "Lost connection"),
    ],
)
def test_match_end_text_covers_each_outcome(
    reason: str, winner: int, me: int, fled: bool, needle: str
) -> None:
    assert needle in match_end_text(reason, winner, me, fled=fled)


def test_match_end_text_is_silent_when_you_fled() -> None:
    # Fleeing already printed "Got away safely!", so the verdict line stays empty.
    assert match_end_text("ko", 1, 0, fled=True) == ""


@pytest.mark.parametrize(
    ("message", "needle"),
    [
        (wire.BattleEnd(winner_slot=0, reason="opponent_left"), "opponent left"),
        (wire.BattleEnd(winner_slot=-1, reason="timeout_draw"), "timed out"),
        (wire.ServerError(code="no_room", message="No such room."), "No such room."),
    ],
)
def test_frame_text_explains_an_early_end(message: BaseModel, needle: str) -> None:
    assert needle in OnlineLobby._frame_text(wire.dump(message))


def test_frame_text_treats_garbage_as_a_lost_connection() -> None:
    assert "Lost connection" in OnlineLobby._frame_text("not json at all")
