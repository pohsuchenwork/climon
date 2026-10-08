"""Core battle data model for climon. Pure data, no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Type(Enum):
    """Elemental type. Covers the types the twelve-Pokemon roster needs."""

    NORMAL = "Normal"
    FIRE = "Fire"
    WATER = "Water"
    GRASS = "Grass"
    POISON = "Poison"
    ELECTRIC = "Electric"
    ICE = "Ice"
    FIGHTING = "Fighting"
    FLYING = "Flying"
    PSYCHIC = "Psychic"
    GHOST = "Ghost"
    DRAGON = "Dragon"


class Category(Enum):
    """Whether a move deals physical damage, special damage, or no damage."""

    PHYSICAL = "Physical"
    SPECIAL = "Special"
    STATUS = "Status"


class Stat(Enum):
    """A battle stat that stage changes can raise or lower."""

    ATTACK = "Attack"
    DEFENSE = "Defense"
    SP_ATTACK = "Sp. Atk"
    SP_DEFENSE = "Sp. Def"
    SPEED = "Speed"


@dataclass(frozen=True)
class Move:
    """A move definition. ``power`` 0 marks a status move; ``accuracy`` 0 never misses."""

    name: str
    type: Type
    category: Category
    power: int
    accuracy: int
    max_pp: int
    effect: str | None = None


@dataclass(frozen=True)
class BaseStats:
    """Species base stats."""

    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int


@dataclass(frozen=True)
class Species:
    """A static Pokemon definition shared by every instance of that species."""

    name: str
    types: tuple[Type, ...]
    base: BaseStats
    moves: tuple[Move, ...]
    sprite_key: str


@dataclass
class Pokemon:
    """A battle instance of a species, with mutable HP, PP, and stat stages."""

    species: Species
    level: int = 50
    current_hp: int = -1
    pp: dict[str, int] = field(default_factory=dict)
    stages: dict[Stat, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.current_hp < 0:
            self.current_hp = self.max_hp
        if not self.pp:
            self.pp = {move.name: move.max_pp for move in self.species.moves}

    @property
    def name(self) -> str:
        return self.species.name

    @property
    def max_hp(self) -> int:
        return (2 * self.species.base.hp * self.level) // 100 + self.level + 10

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def base_stat(self, stat: Stat) -> int:
        """Return the computed stat at this level, before stage modifiers."""
        mapping = {
            Stat.ATTACK: self.species.base.attack,
            Stat.DEFENSE: self.species.base.defense,
            Stat.SP_ATTACK: self.species.base.sp_attack,
            Stat.SP_DEFENSE: self.species.base.sp_defense,
            Stat.SPEED: self.species.base.speed,
        }
        return (2 * mapping[stat] * self.level) // 100 + 5

    def stage(self, stat: Stat) -> int:
        """Return the current stage (-6 to 6) for a stat, defaulting to 0."""
        return self.stages.get(stat, 0)


@dataclass
class Team:
    """A player's team of Pokemon, which one is active, and the item bag."""

    members: list[Pokemon]
    active_index: int = 0
    bag: dict[str, int] = field(default_factory=dict)

    @property
    def active(self) -> Pokemon:
        return self.members[self.active_index]

    @property
    def has_live_member(self) -> bool:
        return any(not member.is_fainted for member in self.members)

    def live_indices(self) -> list[int]:
        """Return the indices of members that have not fainted."""
        return [i for i, member in enumerate(self.members) if not member.is_fainted]


@dataclass
class BattleState:
    """The full, authoritative state of a battle between two teams."""

    teams: tuple[Team, Team]
    turn: int = 0

    def team(self, slot: int) -> Team:
        return self.teams[slot]

    def opponent_of(self, slot: int) -> Team:
        return self.teams[1 - slot]
