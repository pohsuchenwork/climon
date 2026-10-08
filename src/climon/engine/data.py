"""The 12-Pokemon roster, their movesets, and team construction helpers."""

from __future__ import annotations

import random
from collections.abc import Sequence

from climon.engine.items import default_bag
from climon.engine.models import BaseStats, Category, Move, Pokemon, Species, Team, Type

# Moves -------------------------------------------------------------------------
# Normal
TACKLE = Move("Tackle", Type.NORMAL, Category.PHYSICAL, power=40, accuracy=100, max_pp=35)
SCRATCH = Move("Scratch", Type.NORMAL, Category.PHYSICAL, power=40, accuracy=100, max_pp=35)
QUICK_ATTACK = Move(
    "Quick Attack", Type.NORMAL, Category.PHYSICAL, power=40, accuracy=100, max_pp=30
)
BODY_SLAM = Move("Body Slam", Type.NORMAL, Category.PHYSICAL, power=85, accuracy=100, max_pp=15)
BITE = Move("Bite", Type.NORMAL, Category.PHYSICAL, power=60, accuracy=100, max_pp=25)
SWIFT = Move(
    "Swift", Type.NORMAL, Category.SPECIAL, power=60, accuracy=0, max_pp=20
)  # never misses
# Grass
VINE_WHIP = Move("Vine Whip", Type.GRASS, Category.SPECIAL, power=45, accuracy=100, max_pp=25)
# Fire
EMBER = Move("Ember", Type.FIRE, Category.SPECIAL, power=40, accuracy=100, max_pp=25)
FLAMETHROWER = Move("Flamethrower", Type.FIRE, Category.SPECIAL, power=90, accuracy=100, max_pp=15)
# Water
WATER_GUN = Move("Water Gun", Type.WATER, Category.SPECIAL, power=40, accuracy=100, max_pp=25)
SURF = Move("Surf", Type.WATER, Category.SPECIAL, power=90, accuracy=100, max_pp=15)
HYDRO_PUMP = Move("Hydro Pump", Type.WATER, Category.SPECIAL, power=110, accuracy=80, max_pp=5)
# Electric
THUNDERBOLT = Move(
    "Thunderbolt", Type.ELECTRIC, Category.SPECIAL, power=90, accuracy=100, max_pp=15
)
# Ice
ICE_BEAM = Move("Ice Beam", Type.ICE, Category.SPECIAL, power=90, accuracy=100, max_pp=10)
# Fighting
CROSS_CHOP = Move("Cross Chop", Type.FIGHTING, Category.PHYSICAL, power=100, accuracy=80, max_pp=5)
# Flying
WING_ATTACK = Move("Wing Attack", Type.FLYING, Category.PHYSICAL, power=60, accuracy=100, max_pp=35)
# Poison
SLUDGE_BOMB = Move("Sludge Bomb", Type.POISON, Category.SPECIAL, power=90, accuracy=100, max_pp=10)
# Psychic
PSYCHIC = Move("Psychic", Type.PSYCHIC, Category.SPECIAL, power=90, accuracy=100, max_pp=10)
# Ghost
SHADOW_BALL = Move("Shadow Ball", Type.GHOST, Category.SPECIAL, power=80, accuracy=100, max_pp=15)
# Dragon
DRAGON_CLAW = Move("Dragon Claw", Type.DRAGON, Category.PHYSICAL, power=80, accuracy=100, max_pp=15)
# Status
GROWL = Move(
    "Growl", Type.NORMAL, Category.STATUS, power=0, accuracy=100, max_pp=40, effect="lower_attack"
)
TAIL_WHIP = Move(
    "Tail Whip",
    Type.NORMAL,
    Category.STATUS,
    power=0,
    accuracy=100,
    max_pp=30,
    effect="lower_defense",
)

# Species -----------------------------------------------------------------------
BULBASAUR = Species(
    name="Bulbasaur",
    types=(Type.GRASS, Type.POISON),
    base=BaseStats(hp=45, attack=49, defense=49, sp_attack=65, sp_defense=65, speed=45),
    moves=(VINE_WHIP, TACKLE, GROWL),
    sprite_key="bulbasaur",
)
CHARMANDER = Species(
    name="Charmander",
    types=(Type.FIRE,),
    base=BaseStats(hp=39, attack=52, defense=43, sp_attack=60, sp_defense=50, speed=65),
    moves=(EMBER, SCRATCH, GROWL),
    sprite_key="charmander",
)
SQUIRTLE = Species(
    name="Squirtle",
    types=(Type.WATER,),
    base=BaseStats(hp=44, attack=48, defense=65, sp_attack=50, sp_defense=64, speed=43),
    moves=(WATER_GUN, TACKLE, TAIL_WHIP),
    sprite_key="squirtle",
)
CHARIZARD = Species(
    name="Charizard",
    types=(Type.FIRE, Type.FLYING),
    base=BaseStats(hp=78, attack=84, defense=78, sp_attack=109, sp_defense=85, speed=100),
    moves=(FLAMETHROWER, WING_ATTACK, GROWL),
    sprite_key="charizard",
)
PIKACHU = Species(
    name="Pikachu",
    types=(Type.ELECTRIC,),
    base=BaseStats(hp=35, attack=55, defense=40, sp_attack=50, sp_defense=50, speed=90),
    moves=(THUNDERBOLT, QUICK_ATTACK, TAIL_WHIP),
    sprite_key="pikachu",
)
MACHAMP = Species(
    name="Machamp",
    types=(Type.FIGHTING,),
    base=BaseStats(hp=90, attack=130, defense=80, sp_attack=65, sp_defense=85, speed=55),
    moves=(CROSS_CHOP, BODY_SLAM, GROWL),
    sprite_key="machamp",
)
GENGAR = Species(
    name="Gengar",
    types=(Type.GHOST, Type.POISON),
    base=BaseStats(hp=60, attack=65, defense=60, sp_attack=130, sp_defense=75, speed=110),
    moves=(SHADOW_BALL, SLUDGE_BOMB, GROWL),
    sprite_key="gengar",
)
GYARADOS = Species(
    name="Gyarados",
    types=(Type.WATER, Type.FLYING),
    base=BaseStats(hp=95, attack=125, defense=79, sp_attack=60, sp_defense=100, speed=81),
    moves=(HYDRO_PUMP, BITE, TAIL_WHIP),
    sprite_key="gyarados",
)
LAPRAS = Species(
    name="Lapras",
    types=(Type.WATER, Type.ICE),
    base=BaseStats(hp=130, attack=85, defense=80, sp_attack=85, sp_defense=95, speed=60),
    moves=(SURF, ICE_BEAM, GROWL),
    sprite_key="lapras",
)
SNORLAX = Species(
    name="Snorlax",
    types=(Type.NORMAL,),
    base=BaseStats(hp=160, attack=110, defense=65, sp_attack=65, sp_defense=110, speed=30),
    moves=(BODY_SLAM, ICE_BEAM, GROWL),
    sprite_key="snorlax",
)
DRAGONITE = Species(
    name="Dragonite",
    types=(Type.DRAGON, Type.FLYING),
    base=BaseStats(hp=91, attack=134, defense=95, sp_attack=100, sp_defense=100, speed=80),
    moves=(DRAGON_CLAW, WING_ATTACK, GROWL),
    sprite_key="dragonite",
)
MEWTWO = Species(
    name="Mewtwo",
    types=(Type.PSYCHIC,),
    base=BaseStats(hp=106, attack=110, defense=90, sp_attack=154, sp_defense=90, speed=130),
    moves=(PSYCHIC, SWIFT, GROWL),
    sprite_key="mewtwo",
)

# The full roster you draft a team from, and the three original starters.
ROSTER: tuple[Species, ...] = (
    BULBASAUR,
    CHARMANDER,
    SQUIRTLE,
    CHARIZARD,
    PIKACHU,
    MACHAMP,
    GENGAR,
    GYARADOS,
    LAPRAS,
    SNORLAX,
    DRAGONITE,
    MEWTWO,
)
STARTERS: tuple[Species, ...] = (BULBASAUR, CHARMANDER, SQUIRTLE)

TEAM_SIZE = 3


def species_by_name(name: str) -> Species:
    """Return the roster Species matching ``name`` (case-insensitive)."""
    for species in ROSTER:
        if species.name.lower() == name.lower():
            return species
    msg = f"Unknown Pokemon: {name!r}"
    raise KeyError(msg)


def starter_by_name(name: str) -> Species:
    """Back-compatible alias for ``species_by_name``."""
    return species_by_name(name)


def make_team(names: Sequence[str], level: int = 50) -> Team:
    """Build a team from chosen species names; the first name leads."""
    members = [Pokemon(species=species_by_name(name), level=level) for name in names]
    return Team(members=members, active_index=0, bag=default_bag())


def random_team(rng: random.Random, size: int = TEAM_SIZE, level: int = 50) -> Team:
    """Draft a random team of distinct roster species (used by the computer)."""
    picks = rng.sample(ROSTER, k=size)
    members = [Pokemon(species=species, level=level) for species in picks]
    return Team(members=members, active_index=0, bag=default_bag())


def full_team(level: int = 50, lead: str | None = None) -> Team:
    """Build a team of the three original starters, optionally led by ``lead``."""
    members = [Pokemon(species=species, level=level) for species in STARTERS]
    active_index = 0
    if lead is not None:
        target = species_by_name(lead).name
        active_index = next(i for i, member in enumerate(members) if member.name == target)
    return Team(members=members, active_index=active_index, bag=default_bag())
