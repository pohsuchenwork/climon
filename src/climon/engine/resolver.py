"""Turn resolution: the single authoritative step the engine exposes.

``resolve_turn`` mutates the battle state in place and returns the ordered list of
events. After it returns, the caller checks ``needs_replacement`` and, for each
slot, prompts the owner for a ``Replace`` which ``apply_replacement`` carries out.
"""

from __future__ import annotations

import random

from climon.engine.actions import Action, Fight, Run, Switch, UseItem
from climon.engine.events import (
    BattleEnded,
    DamageDealt,
    Event,
    Fainted,
    ItemUsed,
    Missed,
    MoveUsed,
    RunAttempted,
    StatChanged,
    SwitchedIn,
)
from climon.engine.formulas import compute_damage, effective_stat, will_hit
from climon.engine.items import ITEMS
from climon.engine.models import BattleState, Category, Move, Pokemon, Stat


def resolve_turn(
    state: BattleState, actions: tuple[Action, Action], rng: random.Random
) -> list[Event]:
    """Advance the battle by one turn and return what happened."""
    state.turn += 1
    events: list[Event] = []

    # Fleeing ends the battle immediately.
    for slot, action in enumerate(actions):
        if isinstance(action, Run):
            events.append(RunAttempted(slot, success=True))
            events.append(BattleEnded(winner=1 - slot))
            return events

    # Items resolve first (a healed or revived Pokemon is in before attacks land).
    for slot, action in enumerate(actions):
        if isinstance(action, UseItem):
            _apply_item(state, slot, action, events)

    # Voluntary switches resolve before any attack.
    for slot, action in enumerate(actions):
        if isinstance(action, Switch):
            _apply_switch(state, slot, action.target_index, events)

    # Attacks resolve in speed order.
    fighters: list[tuple[int, int]] = [
        (slot, action.move_index)
        for slot, action in enumerate(actions)
        if isinstance(action, Fight)
    ]
    move_by_slot = dict(fighters)
    for slot in _attack_order(state, [slot for slot, _ in fighters], rng):
        if _perform_attack(state, slot, move_by_slot[slot], rng, events):
            return events

    return events


def needs_replacement(state: BattleState) -> list[int]:
    """Return slots whose active Pokemon fainted but still have a live teammate."""
    return [
        slot
        for slot in (0, 1)
        if state.team(slot).active.is_fainted and state.team(slot).has_live_member
    ]


def apply_replacement(state: BattleState, slot: int, target_index: int) -> list[Event]:
    """Send in a live teammate after a faint. Raises if the target has fainted."""
    team = state.team(slot)
    member = team.members[target_index]
    if member.is_fainted:
        msg = f"Cannot send in a fainted Pokemon (index {target_index})"
        raise ValueError(msg)
    team.active_index = target_index
    return [SwitchedIn(slot, member.name)]


def battle_winner(state: BattleState) -> int | None:
    """Return the winning slot if the battle is over, else None."""
    alive = (state.team(0).has_live_member, state.team(1).has_live_member)
    if alive[0] and not alive[1]:
        return 0
    if alive[1] and not alive[0]:
        return 1
    return None


def _attack_order(state: BattleState, slots: list[int], rng: random.Random) -> list[int]:
    if len(slots) <= 1:
        return list(slots)
    first, second = slots[0], slots[1]
    speed_first = effective_stat(state.team(first).active, Stat.SPEED)
    speed_second = effective_stat(state.team(second).active, Stat.SPEED)
    if speed_first > speed_second:
        return [first, second]
    if speed_second > speed_first:
        return [second, first]
    return [first, second] if rng.random() < 0.5 else [second, first]


def _apply_item(state: BattleState, slot: int, action: UseItem, events: list[Event]) -> None:
    """Apply a bag item (heal/revive a member, or boost the active) and consume it."""
    team = state.team(slot)
    item = ITEMS.get(action.item)
    if item is None or team.bag.get(item.name, 0) <= 0:
        return
    if item.boost is not None:
        active = team.active
        current = active.stage(item.boost)
        new = min(6, current + 1)
        if new == current:
            return
        active.stages[item.boost] = new
        team.bag[item.name] -= 1
        events.append(ItemUsed(slot, item.name, active.name, f"{item.boost.value} rose!"))
        return
    if not 0 <= action.target_index < len(team.members):
        return
    target = team.members[action.target_index]
    if item.revive:
        if not target.is_fainted:
            return
        target.current_hp = max(1, target.max_hp // 2)
        team.bag[item.name] -= 1
        events.append(ItemUsed(slot, item.name, target.name, "was revived!"))
        return
    if target.is_fainted:
        return
    before = target.current_hp
    target.current_hp = min(target.max_hp, target.current_hp + item.heal)
    healed = target.current_hp - before
    if healed <= 0:
        return
    team.bag[item.name] -= 1
    events.append(ItemUsed(slot, item.name, target.name, f"restored {healed} HP!"))


def _apply_switch(state: BattleState, slot: int, target_index: int, events: list[Event]) -> None:
    team = state.team(slot)
    member = team.members[target_index]
    if target_index == team.active_index or member.is_fainted:
        return
    team.active_index = target_index
    events.append(SwitchedIn(slot, member.name))


def _perform_attack(
    state: BattleState, attacker_slot: int, move_index: int, rng: random.Random, events: list[Event]
) -> bool:
    """Resolve one attack, appending events. Returns True if the battle ended."""
    attacker = state.team(attacker_slot).active
    if attacker.is_fainted:
        return False  # Knocked out before it could act; its action is lost.

    defender_team = state.opponent_of(attacker_slot)
    defender = defender_team.active
    defender_slot = 1 - attacker_slot
    move = attacker.species.moves[move_index]

    attacker.pp[move.name] = max(0, attacker.pp.get(move.name, 0) - 1)
    events.append(MoveUsed(attacker_slot, attacker.name, move.name))

    if not will_hit(move, rng):
        events.append(Missed(attacker_slot, attacker.name, move.name))
        return False

    if move.category is Category.STATUS:
        _apply_status(move, defender, defender_slot, events)
        return False

    result = compute_damage(attacker, defender, move, rng)
    defender.current_hp = max(0, defender.current_hp - result.amount)
    events.append(
        DamageDealt(
            slot=defender_slot,
            pokemon=defender.name,
            amount=result.amount,
            remaining_hp=defender.current_hp,
            max_hp=defender.max_hp,
            effectiveness=result.effectiveness,
            critical=result.critical,
        )
    )
    if defender.is_fainted:
        events.append(Fainted(defender_slot, defender.name))
        if not defender_team.has_live_member:
            events.append(BattleEnded(winner=attacker_slot))
            return True
    return False


def _apply_status(move: Move, target: Pokemon, target_slot: int, events: list[Event]) -> None:
    if move.effect == "lower_attack":
        _lower_stage(target, Stat.ATTACK, target_slot, events)
    elif move.effect == "lower_defense":
        _lower_stage(target, Stat.DEFENSE, target_slot, events)


def _lower_stage(pokemon: Pokemon, stat: Stat, slot: int, events: list[Event]) -> None:
    current = pokemon.stage(stat)
    new = max(-6, current - 1)
    if new != current:
        pokemon.stages[stat] = new
        events.append(StatChanged(slot, pokemon.name, stat.value, new - current))
