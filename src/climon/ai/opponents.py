"""Computer opponents that choose actions for a battle slot.

RandomAI picks at random; GreedyAI prefers the move that does the most damage right
now (so it avoids resisted moves and reaches for super-effective ones) and sends in
the best type matchup when forced to replace.
"""

from __future__ import annotations

import random
from typing import Protocol

from climon.engine.actions import Action, Fight
from climon.engine.models import BattleState, Category, Move, Pokemon
from climon.engine.types_chart import effectiveness


class Opponent(Protocol):
    """Chooses a turn action and a replacement for a battle slot."""

    def choose(self, state: BattleState, slot: int, rng: random.Random) -> Action: ...

    def choose_replacement(self, state: BattleState, slot: int, rng: random.Random) -> int: ...


class RandomAI:
    """Picks a random move, and a random live teammate when forced to replace."""

    def choose(self, state: BattleState, slot: int, rng: random.Random) -> Action:
        active = state.team(slot).active
        return Fight(rng.randrange(len(active.species.moves)))

    def choose_replacement(self, state: BattleState, slot: int, rng: random.Random) -> int:
        return rng.choice(state.team(slot).live_indices())


class GreedyAI:
    """Picks the highest-scoring move and the best matchup when forced to replace."""

    def choose(self, state: BattleState, slot: int, rng: random.Random) -> Action:
        attacker = state.team(slot).active
        defender = state.opponent_of(slot).active
        moves = attacker.species.moves
        best = max(range(len(moves)), key=lambda i: self._move_score(moves[i], attacker, defender))
        return Fight(best)

    def choose_replacement(self, state: BattleState, slot: int, rng: random.Random) -> int:
        defender = state.opponent_of(slot).active
        team = state.team(slot)
        return max(team.live_indices(), key=lambda i: self._matchup(team.members[i], defender))

    @staticmethod
    def _move_score(move: Move, attacker: Pokemon, defender: Pokemon) -> float:
        if move.category is Category.STATUS:
            return 1.0
        stab = 1.5 if move.type in attacker.species.types else 1.0
        return move.power * stab * effectiveness(move.type, defender.species.types)

    @staticmethod
    def _matchup(member: Pokemon, defender: Pokemon) -> float:
        return max(
            (
                effectiveness(move.type, defender.species.types)
                for move in member.species.moves
                if move.power > 0
            ),
            default=1.0,
        )
