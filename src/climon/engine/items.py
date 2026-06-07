"""Battle items: the six bag items, their effects, and the default loadout.

Pure data plus small helpers; the resolver applies the effects and the bag (a
name -> count map on each Team) tracks what is left. Using an item takes the turn.
"""

from __future__ import annotations

from dataclasses import dataclass

from climon.engine.models import Stat

FULL_HEAL = 9999


@dataclass(frozen=True)
class Item:
    """An item definition. Exactly one of heal/revive/boost is meaningful."""

    name: str
    description: str
    heal: int = 0  # HP restored to a chosen member (FULL_HEAL = restore all)
    revive: bool = False  # revive a fainted member with half HP
    boost: Stat | None = None  # raise the active Pokemon's stat one stage


ITEMS: dict[str, Item] = {
    "Potion": Item("Potion", "Restore 20 HP to a Pokemon.", heal=20),
    "Super Potion": Item("Super Potion", "Restore 60 HP to a Pokemon.", heal=60),
    "Hyper Potion": Item("Hyper Potion", "Restore 120 HP to a Pokemon.", heal=120),
    "Full Restore": Item("Full Restore", "Fully restore a Pokemon's HP.", heal=FULL_HEAL),
    "Revive": Item("Revive", "Revive a fainted Pokemon with half HP.", revive=True),
    "X Attack": Item("X Attack", "Raise the active Pokemon's Attack one stage.", boost=Stat.ATTACK),
}

ITEM_ORDER: tuple[str, ...] = tuple(ITEMS)


def default_bag() -> dict[str, int]:
    """A fresh starting bag (counts per item)."""
    return {
        "Potion": 2,
        "Super Potion": 1,
        "Hyper Potion": 1,
        "Full Restore": 1,
        "Revive": 1,
        "X Attack": 1,
    }


def needs_target(item: Item) -> bool:
    """True if the item is used on a chosen member (heal/revive); boosts hit the active."""
    return item.boost is None
