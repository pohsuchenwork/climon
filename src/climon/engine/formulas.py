"""Damage, accuracy, and stat-stage math. All randomness comes from an injected RNG.

Keeping every random draw on the passed-in ``random.Random`` is what makes the
engine deterministic: the same state, move, and seed always give the same result.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from climon.engine.models import Category, Move, Pokemon, Stat
from climon.engine.types_chart import effectiveness

CRIT_CHANCE = 1 / 24
CRIT_MULTIPLIER = 1.5


@dataclass(frozen=True)
class DamageResult:
    amount: int
    effectiveness: float
    critical: bool


def stage_multiplier(stage: int) -> float:
    """Return the Pokemon stat-stage multiplier for a stage in the range -6 to 6."""
    stage = max(-6, min(6, stage))
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)


def effective_stat(pokemon: Pokemon, stat: Stat) -> float:
    """Return a Pokemon's stat at its level, with its current stage applied."""
    return pokemon.base_stat(stat) * stage_multiplier(pokemon.stage(stat))


def will_hit(move: Move, rng: random.Random) -> bool:
    """Return whether the move lands. Accuracy 0 always hits."""
    if move.accuracy == 0:
        return True
    return rng.randint(1, 100) <= move.accuracy


def compute_damage(
    attacker: Pokemon, defender: Pokemon, move: Move, rng: random.Random
) -> DamageResult:
    """Compute damage for one landed attacking move using the classic formula."""
    type_mult = effectiveness(move.type, defender.species.types)
    if type_mult == 0.0 or move.power == 0:
        return DamageResult(0, type_mult, False)

    if move.category is Category.PHYSICAL:
        attack = effective_stat(attacker, Stat.ATTACK)
        defense = effective_stat(defender, Stat.DEFENSE)
    else:
        attack = effective_stat(attacker, Stat.SP_ATTACK)
        defense = effective_stat(defender, Stat.SP_DEFENSE)

    base = ((2 * attacker.level / 5 + 2) * move.power * attack / defense) / 50 + 2
    stab = 1.5 if move.type in attacker.species.types else 1.0
    critical = rng.random() < CRIT_CHANCE
    crit = CRIT_MULTIPLIER if critical else 1.0
    roll = rng.randint(85, 100) / 100
    amount = math.floor(base * stab * type_mult * crit * roll)
    return DamageResult(max(1, amount), type_mult, critical)
