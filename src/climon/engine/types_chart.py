"""Type effectiveness for the roster's types. Anything unlisted is neutral (1.0)."""

from __future__ import annotations

from climon.engine.models import Type

# Attacker type -> defender type -> multiplier. Missing pairs default to 1.0.
# Only the types the 12-Pokemon roster uses are listed (no Ground/Rock/Bug/etc.).
_CHART: dict[tuple[Type, Type], float] = {
    # Normal
    (Type.NORMAL, Type.GHOST): 0.0,
    # Fire
    (Type.FIRE, Type.GRASS): 2.0,
    (Type.FIRE, Type.ICE): 2.0,
    (Type.FIRE, Type.FIRE): 0.5,
    (Type.FIRE, Type.WATER): 0.5,
    (Type.FIRE, Type.DRAGON): 0.5,
    # Water
    (Type.WATER, Type.FIRE): 2.0,
    (Type.WATER, Type.WATER): 0.5,
    (Type.WATER, Type.GRASS): 0.5,
    (Type.WATER, Type.DRAGON): 0.5,
    # Grass
    (Type.GRASS, Type.WATER): 2.0,
    (Type.GRASS, Type.FIRE): 0.5,
    (Type.GRASS, Type.GRASS): 0.5,
    (Type.GRASS, Type.POISON): 0.5,
    (Type.GRASS, Type.FLYING): 0.5,
    (Type.GRASS, Type.DRAGON): 0.5,
    # Electric
    (Type.ELECTRIC, Type.WATER): 2.0,
    (Type.ELECTRIC, Type.FLYING): 2.0,
    (Type.ELECTRIC, Type.ELECTRIC): 0.5,
    (Type.ELECTRIC, Type.GRASS): 0.5,
    (Type.ELECTRIC, Type.DRAGON): 0.5,
    # Ice
    (Type.ICE, Type.GRASS): 2.0,
    (Type.ICE, Type.FLYING): 2.0,
    (Type.ICE, Type.DRAGON): 2.0,
    (Type.ICE, Type.FIRE): 0.5,
    (Type.ICE, Type.WATER): 0.5,
    (Type.ICE, Type.ICE): 0.5,
    # Fighting
    (Type.FIGHTING, Type.NORMAL): 2.0,
    (Type.FIGHTING, Type.ICE): 2.0,
    (Type.FIGHTING, Type.POISON): 0.5,
    (Type.FIGHTING, Type.FLYING): 0.5,
    (Type.FIGHTING, Type.PSYCHIC): 0.5,
    (Type.FIGHTING, Type.GHOST): 0.0,
    # Poison
    (Type.POISON, Type.GRASS): 2.0,
    (Type.POISON, Type.POISON): 0.5,
    (Type.POISON, Type.GHOST): 0.5,
    # Flying
    (Type.FLYING, Type.GRASS): 2.0,
    (Type.FLYING, Type.FIGHTING): 2.0,
    (Type.FLYING, Type.ELECTRIC): 0.5,
    # Psychic
    (Type.PSYCHIC, Type.FIGHTING): 2.0,
    (Type.PSYCHIC, Type.POISON): 2.0,
    (Type.PSYCHIC, Type.PSYCHIC): 0.5,
    # Ghost
    (Type.GHOST, Type.GHOST): 2.0,
    (Type.GHOST, Type.PSYCHIC): 2.0,
    (Type.GHOST, Type.NORMAL): 0.0,
    # Dragon
    (Type.DRAGON, Type.DRAGON): 2.0,
}


def effectiveness(attack_type: Type, defender_types: tuple[Type, ...]) -> float:
    """Return the combined type multiplier of a move against a defender's types."""
    multiplier = 1.0
    for defender_type in defender_types:
        multiplier *= _CHART.get((attack_type, defender_type), 1.0)
    return multiplier
