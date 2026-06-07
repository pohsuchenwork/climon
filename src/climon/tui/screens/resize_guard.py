"""A modal that covers the battle when the terminal is too small to show it whole.

The battle is designed to fit on one screen without scrolling, which needs about
80x28. Below that, this guard takes over and pauses play until the user resizes,
so the classic full-screen layout is never shown clipped.
"""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static

MIN_WIDTH = 80
MIN_HEIGHT = 28

_GUARD_TEXT = (
    "Terminal too small\n\n"
    f"climon needs at least {MIN_WIDTH} x {MIN_HEIGHT}.\n"
    "Resize the window to return to the battle."
)


def big_enough(width: int, height: int) -> bool:
    """True when the terminal can show the whole battle without scrolling."""
    return width >= MIN_WIDTH and height >= MIN_HEIGHT


class ResizeGuard(ModalScreen[None]):
    """Shown over the battle while the terminal is below the minimum size."""

    def compose(self) -> ComposeResult:
        yield Static(_GUARD_TEXT, id="resize-guard")

    def on_resize(self, event: events.Resize) -> None:
        if big_enough(event.size.width, event.size.height):
            self.app.pop_screen()
