"""Type effectiveness tests across the roster's types, including dual-type stacking."""

from __future__ import annotations

import pytest

from climon.engine.models import Type
from climon.engine.types_chart import effectiveness


@pytest.mark.parametrize(
    ("attack_type", "defender_types", "expected"),
    [
        # Starter triangle
        (Type.FIRE, (Type.GRASS,), 2.0),
        (Type.FIRE, (Type.WATER,), 0.5),
        (Type.WATER, (Type.FIRE,), 2.0),
        (Type.GRASS, (Type.WATER,), 2.0),
        # Neutral and immunities
        (Type.NORMAL, (Type.GRASS,), 1.0),
        (Type.NORMAL, (Type.GHOST,), 0.0),
        (Type.GHOST, (Type.NORMAL,), 0.0),
        (Type.FIGHTING, (Type.GHOST,), 0.0),
        # New single-type matchups
        (Type.GHOST, (Type.PSYCHIC,), 2.0),
        (Type.ELECTRIC, (Type.WATER,), 2.0),
        (Type.ELECTRIC, (Type.FLYING,), 2.0),
        (Type.ICE, (Type.DRAGON,), 2.0),
        (Type.FIGHTING, (Type.NORMAL,), 2.0),
        (Type.FIGHTING, (Type.PSYCHIC,), 0.5),
        (Type.PSYCHIC, (Type.POISON,), 2.0),
        (Type.WATER, (Type.DRAGON,), 0.5),
        # Dual-type stacking
        (Type.ELECTRIC, (Type.WATER, Type.FLYING), 4.0),  # Gyarados is doubly weak
        (Type.ICE, (Type.DRAGON, Type.FLYING), 4.0),  # Dragonite is doubly weak
        (Type.GRASS, (Type.GRASS, Type.POISON), 0.25),  # Bulbasaur resists it twice
        (Type.FIRE, (Type.GRASS, Type.POISON), 2.0),
    ],
)
def test_effectiveness(
    attack_type: Type, defender_types: tuple[Type, ...], expected: float
) -> None:
    assert effectiveness(attack_type, defender_types) == expected
