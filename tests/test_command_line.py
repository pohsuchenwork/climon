"""Tests for the typed battle-command parser and submenu match helpers."""

from __future__ import annotations

from climon.engine.actions import Fight, Run, Switch
from climon.engine.data import BULBASAUR, full_team
from climon.engine.models import Pokemon
from climon.tui.command_line import match_member, match_move, parse_command


def _bulbasaur() -> Pokemon:
    # Moves: Vine Whip (0), Tackle (1), Growl (2).
    return Pokemon(BULBASAUR)


def test_attack_defaults_to_first_move() -> None:
    assert parse_command("attack", _bulbasaur()) == Fight(0)


def test_fight_with_index() -> None:
    assert parse_command("fight 2", _bulbasaur()) == Fight(1)


def test_move_by_name() -> None:
    assert parse_command("vine whip", _bulbasaur()) == Fight(0)
    assert parse_command("tackle", _bulbasaur()) == Fight(1)


def test_run() -> None:
    assert parse_command("run", _bulbasaur()) == Run()


def test_switch() -> None:
    assert parse_command("switch 2", _bulbasaur()) == Switch(1)


def test_unknown_returns_none() -> None:
    assert parse_command("xyzzy", _bulbasaur()) is None


def test_out_of_range_move_index_returns_none() -> None:
    assert parse_command("fight 9", _bulbasaur()) is None


def test_empty_returns_none() -> None:
    assert parse_command("   ", _bulbasaur()) is None


def test_parse_is_case_insensitive() -> None:
    assert parse_command("TACKLE", _bulbasaur()) == Fight(1)
    assert parse_command("FiGhT 1", _bulbasaur()) == Fight(0)


def test_match_move_number_and_name() -> None:
    assert match_move("2", _bulbasaur()) == 1
    assert match_move("VINE WHIP", _bulbasaur()) == 0
    assert match_move("nope", _bulbasaur()) is None


def test_match_member_number_and_name() -> None:
    team = full_team(lead="Bulbasaur")
    assert match_member("2", team) == 1
    assert match_member("squirtle", team) == 2
    assert match_member("SQUIRTLE", team) == 2
    assert match_member("nope", team) is None
