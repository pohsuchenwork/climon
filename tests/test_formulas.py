"""Damage, accuracy, and stat-stage math tests. All deterministic via seeded RNG."""

from __future__ import annotations

import random

import pytest

from climon.engine.data import BULBASAUR, CHARMANDER, EMBER, SQUIRTLE
from climon.engine.formulas import compute_damage, stage_multiplier, will_hit
from climon.engine.models import Category, Move, Pokemon, Type


@pytest.mark.parametrize(
    ("stage", "expected"),
    [(0, 1.0), (1, 1.5), (2, 2.0), (6, 4.0), (-1, 2 / 3), (-6, 0.25)],
)
def test_stage_multiplier(stage: int, expected: float) -> None:
    assert stage_multiplier(stage) == pytest.approx(expected)


def test_effectiveness_recorded_in_result() -> None:
    rng = random.Random(0)
    strong = compute_damage(Pokemon(CHARMANDER), Pokemon(BULBASAUR), EMBER, rng)
    weak = compute_damage(Pokemon(CHARMANDER), Pokemon(SQUIRTLE), EMBER, rng)
    assert strong.effectiveness == 2.0
    assert weak.effectiveness == 0.5


def test_damage_within_range() -> None:
    defender = Pokemon(BULBASAUR)
    result = compute_damage(Pokemon(CHARMANDER), defender, EMBER, random.Random(5))
    assert 1 <= result.amount < defender.max_hp


def test_damage_is_deterministic() -> None:
    first = compute_damage(Pokemon(CHARMANDER), Pokemon(BULBASAUR), EMBER, random.Random(9))
    second = compute_damage(Pokemon(CHARMANDER), Pokemon(BULBASAUR), EMBER, random.Random(9))
    assert first == second


def test_accuracy_zero_always_hits() -> None:
    never_miss = Move("Sure", Type.NORMAL, Category.PHYSICAL, power=10, accuracy=0, max_pp=5)
    assert all(will_hit(never_miss, random.Random(seed)) for seed in range(20))


def test_imperfect_accuracy_is_deterministic() -> None:
    flaky = Move("Flaky", Type.NORMAL, Category.PHYSICAL, power=10, accuracy=50, max_pp=5)
    assert will_hit(flaky, random.Random(1)) == will_hit(flaky, random.Random(1))
