"""Tests for the computer opponents."""

from __future__ import annotations

import random

from climon.ai.opponents import GreedyAI
from climon.engine.actions import Fight
from climon.engine.data import BULBASAUR, CHARMANDER, SQUIRTLE
from climon.engine.models import BattleState, Pokemon, Species, Team


def _duel(attacker: Species, defender: Species) -> BattleState:
    return BattleState(teams=(Team([Pokemon(attacker)]), Team([Pokemon(defender)])))


def test_greedy_picks_super_effective_move() -> None:
    # Charmander vs Bulbasaur: Ember (Fire, move 0) is super-effective.
    state = _duel(CHARMANDER, BULBASAUR)
    assert GreedyAI().choose(state, 0, random.Random(1)) == Fight(0)


def test_greedy_avoids_a_resisted_move() -> None:
    # Charmander vs Squirtle (Water resists Fire): pick Scratch (Normal, move 1), not Ember.
    state = _duel(CHARMANDER, SQUIRTLE)
    assert GreedyAI().choose(state, 0, random.Random(1)) == Fight(1)


def test_greedy_replacement_picks_best_matchup() -> None:
    team = Team([Pokemon(SQUIRTLE), Pokemon(CHARMANDER)])
    state = BattleState(teams=(team, Team([Pokemon(BULBASAUR)])))
    index = GreedyAI().choose_replacement(state, 0, random.Random(1))
    assert team.members[index].name == "Charmander"  # Fire beats the opposing Grass
