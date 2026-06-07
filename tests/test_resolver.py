"""Turn-resolution tests: order, switching, status, faint, replacement, win, run."""

from __future__ import annotations

import random

from climon.engine.actions import Fight, Run, Switch
from climon.engine.data import BULBASAUR, CHARMANDER, SQUIRTLE
from climon.engine.events import (
    BattleEnded,
    DamageDealt,
    Fainted,
    MoveUsed,
    StatChanged,
    SwitchedIn,
)
from climon.engine.models import BattleState, Pokemon, Species, Stat, Team
from climon.engine.resolver import (
    apply_replacement,
    battle_winner,
    needs_replacement,
    resolve_turn,
)


def _mon(species: Species, hp: int | None = None, level: int = 50) -> Pokemon:
    pokemon = Pokemon(species=species, level=level)
    if hp is not None:
        pokemon.current_hp = hp
    return pokemon


def _state(team0: Team, team1: Team) -> BattleState:
    return BattleState(teams=(team0, team1))


def test_faster_pokemon_attacks_first() -> None:
    state = _state(Team([_mon(CHARMANDER)]), Team([_mon(BULBASAUR)]))
    events = resolve_turn(state, (Fight(0), Fight(0)), random.Random(1))
    moves = [event for event in events if isinstance(event, MoveUsed)]
    assert moves[0].pokemon == "Charmander"  # speed 65 beats 45


def test_super_effective_faints_and_wins() -> None:
    state = _state(Team([_mon(CHARMANDER)]), Team([_mon(BULBASAUR, hp=10)]))
    events = resolve_turn(state, (Fight(0), Fight(0)), random.Random(1))
    assert any(isinstance(e, Fainted) and e.pokemon == "Bulbasaur" for e in events)
    assert BattleEnded(winner=0) in events
    assert battle_winner(state) == 0


def test_switch_resolves_before_opponent_attack() -> None:
    team0 = Team([_mon(CHARMANDER), _mon(SQUIRTLE)], active_index=0)
    state = _state(team0, Team([_mon(BULBASAUR)]))
    events = resolve_turn(state, (Switch(1), Fight(0)), random.Random(3))
    assert state.team(0).active.name == "Squirtle"
    switched = [e for e in events if isinstance(e, SwitchedIn)]
    damaged = [e for e in events if isinstance(e, DamageDealt)]
    assert switched[0].pokemon == "Squirtle"
    assert damaged[0].pokemon == "Squirtle"  # Vine Whip hit the new active


def test_growl_lowers_target_attack() -> None:
    state = _state(Team([_mon(CHARMANDER)]), Team([_mon(BULBASAUR)]))
    events = resolve_turn(state, (Fight(2), Fight(1)), random.Random(2))
    assert any(isinstance(e, StatChanged) and e.stat == "Attack" and e.delta == -1 for e in events)
    assert state.team(1).active.stage(Stat.ATTACK) == -1


def test_faint_forces_replacement_with_live_members() -> None:
    team1 = Team([_mon(BULBASAUR, hp=5), _mon(SQUIRTLE)], active_index=0)
    state = _state(Team([_mon(CHARMANDER)]), team1)
    events = resolve_turn(state, (Fight(0), Fight(0)), random.Random(1))
    assert any(isinstance(e, Fainted) and e.pokemon == "Bulbasaur" for e in events)
    assert battle_winner(state) is None
    assert needs_replacement(state) == [1]
    replaced = apply_replacement(state, 1, 1)
    assert state.team(1).active.name == "Squirtle"
    assert any(isinstance(e, SwitchedIn) for e in replaced)


def test_run_ends_the_battle() -> None:
    state = _state(Team([_mon(CHARMANDER)]), Team([_mon(BULBASAUR)]))
    events = resolve_turn(state, (Run(), Fight(0)), random.Random(1))
    assert BattleEnded(winner=1) in events


def test_pp_decrements_on_use() -> None:
    charmander = _mon(CHARMANDER)
    state = _state(Team([charmander]), Team([_mon(BULBASAUR)]))
    before = charmander.pp["Ember"]
    resolve_turn(state, (Fight(0), Fight(0)), random.Random(1))
    assert charmander.pp["Ember"] == before - 1


def test_resolution_is_deterministic() -> None:
    def run() -> object:
        state = _state(
            Team([_mon(CHARMANDER), _mon(SQUIRTLE), _mon(BULBASAUR)]),
            Team([_mon(BULBASAUR), _mon(CHARMANDER), _mon(SQUIRTLE)]),
        )
        return resolve_turn(state, (Fight(0), Fight(0)), random.Random(42))

    assert run() == run()
