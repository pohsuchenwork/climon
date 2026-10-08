"""The classic 2x2 command menu.

The four cells normally read FIGHT / BAG / POKEMON / RUN, but they are updated to
show the current submenu's options (moves, team members, yes/no) and `reset` back.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Static

MAIN_COMMANDS = ("FIGHT", "BAG", "POKEMON", "RUN")


class CommandGrid(Grid):
    """A 2x2 grid whose cells reflect the current command options."""

    def compose(self) -> ComposeResult:
        for command in MAIN_COMMANDS:
            yield Static(command, classes="command-cell")

    def set_options(self, labels: list[str]) -> None:
        """Set the four cell labels, padded or truncated to four."""
        padded = ([*labels, "", "", ""])[:4]
        for cell, label in zip(self.query(Static), padded, strict=False):
            cell.update(label)

    def reset(self) -> None:
        """Restore the four standard commands."""
        self.set_options(list(MAIN_COMMANDS))
