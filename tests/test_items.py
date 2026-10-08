"""Tests for usable battle items: effects, turn order, and bag consumption."""

from __future__ import annotations

import random

from climon.engine.actions import Fight, UseItem
from climon.engine.data import make_team
from climon.engine.events import DamageDealt, ItemUsed
from climon.engine.items import ITEMS, default_bag, needs_target
from climon.engine.models import BattleState, Stat
from climon.engine.resolver import resolve_turn


def _battle() -> BattleState:
    return BattleState(
        teams=(
            make_team(["Snorlax", "Pikachu", "Gengar"]),
            make_team(["Charizard", "Gyarados", "Lapras"]),
        )
    )


def test_potion_heals_and_is_consumed() -> None:
    state = _battle()
    snorlax = state.team(0).active
    snorlax.current_hp = snorlax.max_hp - 50
    before = state.team(0).bag["Potion"]
    events = resolve_turn(state, (UseItem("Potion", 0), Fight(2)), random.Random(0))
    assert snorlax.current_hp == snorlax.max_hp - 30  # healed 20
    assert state.team(0).bag["Potion"] == before - 1
    assert any(isinstance(event, ItemUsed) for event in events)


def test_full_restore_caps_at_max_hp() -> None:
    state = _battle()
    active = state.team(0).active
    active.current_hp = 1
    resolve_turn(state, (UseItem("Full Restore", 0), Fight(2)), random.Random(0))
    assert active.current_hp == active.max_hp


def test_revive_brings_back_a_fainted_member() -> None:
    state = _battle()
    bench = state.team(0).members[1]
    bench.current_hp = 0
    assert bench.is_fainted
    resolve_turn(state, (UseItem("Revive", 1), Fight(0)), random.Random(0))
    assert not bench.is_fainted
    assert bench.current_hp == bench.max_hp // 2


def test_x_attack_raises_attack_stage() -> None:
    state = _battle()
    active = state.team(0).active
    assert active.stage(Stat.ATTACK) == 0
    resolve_turn(state, (UseItem("X Attack", 0), Fight(0)), random.Random(0))
    assert active.stage(Stat.ATTACK) == 1


def test_using_an_item_takes_the_turn_and_resolves_before_attacks() -> None:
    state = _battle()
    me = state.team(0).active
    me.current_hp = me.max_hp - 100
    events = resolve_turn(state, (UseItem("Hyper Potion", 0), Fight(0)), random.Random(0))
    item_index = next(i for i, event in enumerate(events) if isinstance(event, ItemUsed))
    hits_on_me = [
        i for i, event in enumerate(events) if isinstance(event, DamageDealt) and event.slot == 0
    ]
    assert hits_on_me, "the opponent should still attack on a turn I spent on an item"
    assert item_index < hits_on_me[0]


def test_heal_on_full_hp_does_nothing_and_is_not_consumed() -> None:
    state = _battle()
    before = state.team(0).bag["Potion"]
    events = resolve_turn(state, (UseItem("Potion", 0), Fight(2)), random.Random(0))
    assert state.team(0).bag["Potion"] == before
    assert not any(isinstance(event, ItemUsed) for event in events)


def test_default_bag_and_needs_target() -> None:
    assert sum(default_bag().values()) >= 6
    assert needs_target(ITEMS["Potion"]) is True
    assert needs_target(ITEMS["X Attack"]) is False
