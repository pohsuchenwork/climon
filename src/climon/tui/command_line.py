"""Parse typed battle commands and submenu selections. Case-insensitive throughout."""

from __future__ import annotations

from climon.engine.actions import Action, Fight, Run, Switch
from climon.engine.models import Pokemon, Team


def parse_command(text: str, active: Pokemon) -> Action | None:
    """Turn a main-menu command into an Action, or None if it is not understood."""
    parts = text.strip().lower().split()
    if not parts:
        return None
    head, rest = parts[0], parts[1:]
    if head in ("fight", "attack", "a", "f"):
        index = _move_index(rest, active) if rest else 0
        return Fight(index) if index is not None else None
    if head in ("switch", "swap", "sw"):
        if rest and rest[0].isdigit():
            return Switch(int(rest[0]) - 1)
        return None
    if head in ("run", "flee"):
        return Run()
    index = _move_index(parts, active)
    return Fight(index) if index is not None else None


def match_move(text: str, active: Pokemon) -> int | None:
    """Return a move index for a number or a (case-insensitive) move name."""
    return _move_index(text.strip().lower().split(), active)


def match_member(text: str, team: Team) -> int | None:
    """Return a team index for a number or a (case-insensitive) Pokemon name."""
    tokens = text.strip().lower().split()
    if not tokens:
        return None
    if tokens[0].isdigit():
        index = int(tokens[0]) - 1
        return index if 0 <= index < len(team.members) else None
    name = " ".join(tokens)
    for index, member in enumerate(team.members):
        if member.name.lower() == name or member.name.lower().startswith(name):
            return index
    return None


def _move_index(tokens: list[str], active: Pokemon) -> int | None:
    if not tokens:
        return None
    if tokens[0].isdigit():
        index = int(tokens[0]) - 1
        return index if 0 <= index < len(active.species.moves) else None
    name = " ".join(tokens)
    for index, move in enumerate(active.species.moves):
        if move.name.lower() == name or move.name.lower().startswith(name):
            return index
    return None
