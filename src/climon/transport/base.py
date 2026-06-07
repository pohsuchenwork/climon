"""The BattleSession interface the battle screen talks to.

LocalSession (PvC) runs the engine in-process; NetworkSession (PvP, later) relays
actions to the server. The battle screen depends only on this protocol, so one
screen serves both modes.
"""

from __future__ import annotations

from typing import Protocol

from climon.engine.actions import Action
from climon.engine.events import Event
from climon.engine.models import BattleState


class BattleSession(Protocol):
    """A live battle the UI can read, submit actions to, and replace fainted Pokemon in."""

    @property
    def state(self) -> BattleState: ...

    @property
    def player_slot(self) -> int: ...

    @property
    def winner(self) -> int | None: ...

    async def submit(self, action: Action) -> list[Event]:
        """Submit the player's action for the turn and return the resulting events."""
        ...

    async def replace(self, target_index: int) -> list[Event]:
        """Send in a live teammate after the player's active faints."""
        ...

    async def close(self) -> None:
        """Release resources (e.g. close the network connection) when leaving."""
        ...
