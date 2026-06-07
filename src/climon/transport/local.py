"""LocalSession: runs the engine and a computer opponent in-process (PvC)."""

from __future__ import annotations

import random

from climon.ai.opponents import Opponent
from climon.engine.actions import Action
from climon.engine.events import Event
from climon.engine.models import BattleState
from climon.engine.resolver import (
    apply_replacement,
    battle_winner,
    needs_replacement,
    resolve_turn,
)


class LocalSession:
    """A battle against the computer. The player is always slot 0."""

    def __init__(self, state: BattleState, opponent: Opponent, rng: random.Random) -> None:
        self._state = state
        self._opponent = opponent
        self._rng = rng

    @property
    def state(self) -> BattleState:
        return self._state

    @property
    def player_slot(self) -> int:
        return 0

    @property
    def winner(self) -> int | None:
        return battle_winner(self._state)

    async def submit(self, action: Action) -> list[Event]:
        opponent_action = self._opponent.choose(self._state, 1, self._rng)
        events = resolve_turn(self._state, (action, opponent_action), self._rng)
        events.extend(self._auto_replace_opponent())
        return events

    async def replace(self, target_index: int) -> list[Event]:
        return apply_replacement(self._state, 0, target_index)

    async def close(self) -> None:
        """Nothing to release for a local game."""
        return None

    def _auto_replace_opponent(self) -> list[Event]:
        if 1 in needs_replacement(self._state):
            index = self._opponent.choose_replacement(self._state, 1, self._rng)
            return apply_replacement(self._state, 1, index)
        return []
