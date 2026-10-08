"""Actions a player can submit for a turn.

``Switch`` is a voluntary in-turn action that resolves before attacks and uses up
the turn. ``Replace`` is the free switch-in forced after a Pokemon faints; it does
not consume a turn.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fight:
    """Use the active Pokemon's move at ``move_index``."""

    move_index: int


@dataclass(frozen=True)
class Switch:
    """Voluntarily switch the active Pokemon to ``target_index`` (uses the turn)."""

    target_index: int


@dataclass(frozen=True)
class Replace:
    """Send in ``target_index`` after a faint (free, does not use a turn)."""

    target_index: int


@dataclass(frozen=True)
class UseItem:
    """Use a bag item on a team member (heal/revive) or the active (boost); uses the turn."""

    item: str
    target_index: int = 0


@dataclass(frozen=True)
class Run:
    """Flee the battle (forfeit in PvP)."""


Action = Fight | Switch | Replace | Run | UseItem
