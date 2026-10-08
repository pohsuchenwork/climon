"""Tests for the local PvC battle session."""

from __future__ import annotations

import random

from climon.ai.opponents import RandomAI
from climon.engine.actions import Fight
from climon.engine.data import full_team
from climon.engine.models import BattleState
from climon.engine.resolver import needs_replacement
from climon.transport.local import LocalSession


def _session(seed: int) -> LocalSession:
    state = BattleState(teams=(full_team(lead="Bulbasaur"), full_team(lead="Charmander")))
    return LocalSession(state, RandomAI(), random.Random(seed))


async def test_one_turn_produces_events_and_advances() -> None:
    session = _session(1)
    events = await session.submit(Fight(0))
    assert events
    assert session.state.turn == 1
    assert session.player_slot == 0


async def test_battle_runs_to_a_winner() -> None:
    session = _session(7)
    for _ in range(300):
        if session.winner is not None:
            break
        if session.player_slot in needs_replacement(session.state):
            live = session.state.team(session.player_slot).live_indices()
            await session.replace(live[0])
            continue
        await session.submit(Fight(0))
    assert session.winner is not None
