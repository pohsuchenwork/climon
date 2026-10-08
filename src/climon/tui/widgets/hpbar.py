"""An HP bar that shifts color green to yellow to red and shows numeric HP.

The fill eases toward new values (a short drain animation) unless the caller asks
for an instant update (reduce-motion). The color is always paired with the numeric
value so meaning never depends on color alone.
"""

from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

from climon.tui.display import hp_glyphs

BAR_WIDTH = 16
DRAIN_SECONDS = 0.35


class HPBar(Static):
    """A fixed-width HP bar for one Pokemon."""

    pct: reactive[float] = reactive(1.0)

    def __init__(self, current: int, maximum: int, *, id: str | None = None) -> None:
        self._maximum = max(1, maximum)
        super().__init__(id=id)
        self.set_reactive(HPBar.pct, max(0.0, min(1.0, current / self._maximum)))

    def set_hp(self, current: int, maximum: int, *, animate: bool = True) -> None:
        self._maximum = max(1, maximum)
        target = max(0.0, min(1.0, current / self._maximum))
        if animate:
            self.animate("pct", value=target, duration=DRAIN_SECONDS)
        else:
            self.pct = target

    def watch_pct(self) -> None:
        self.refresh()

    def render(self) -> Text:
        ratio = max(0.0, min(1.0, self.pct))
        filled = round(ratio * BAR_WIDTH)
        current = round(ratio * self._maximum)
        color = "green" if ratio > 0.5 else "yellow" if ratio > 0.2 else "red"
        full, empty = hp_glyphs()
        bar = Text()
        bar.append("HP ", style="bold")
        bar.append(full * filled, style=color)
        bar.append(empty * (BAR_WIDTH - filled), style="grey37")
        bar.append(f" {current}/{self._maximum}")
        return bar
