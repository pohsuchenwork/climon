"""Events describing what happened during a turn.

The UI, the message log, and the network layer all render battles from this
ordered event stream, so they never need to diff raw state. ``slot`` identifies a
player (0 or 1); damage and faint events use the affected (defending) slot.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveUsed:
    slot: int
    pokemon: str
    move: str


@dataclass(frozen=True)
class Missed:
    slot: int
    pokemon: str
    move: str


@dataclass(frozen=True)
class DamageDealt:
    slot: int
    pokemon: str
    amount: int
    remaining_hp: int
    max_hp: int
    effectiveness: float
    critical: bool


@dataclass(frozen=True)
class StatChanged:
    slot: int
    pokemon: str
    stat: str
    delta: int


@dataclass(frozen=True)
class Fainted:
    slot: int
    pokemon: str


@dataclass(frozen=True)
class SwitchedIn:
    slot: int
    pokemon: str


@dataclass(frozen=True)
class RunAttempted:
    slot: int
    success: bool


@dataclass(frozen=True)
class ItemUsed:
    slot: int
    item: str
    target: str
    detail: str


@dataclass(frozen=True)
class BattleEnded:
    winner: int


Event = (
    MoveUsed
    | Missed
    | DamageDealt
    | StatChanged
    | Fainted
    | SwitchedIn
    | ItemUsed
    | RunAttempted
    | BattleEnded
)
