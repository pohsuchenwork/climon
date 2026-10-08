"""Round-trip tests for the online wire protocol."""

from __future__ import annotations

import random

import pytest
from pydantic import ValidationError

from climon.engine.actions import Fight, Run, Switch
from climon.engine.data import full_team
from climon.engine.models import BattleState
from climon.engine.resolver import resolve_turn
from climon.protocol import messages as m


def test_client_messages_round_trip() -> None:
    originals = [
        m.Hello(name="Ada"),
        m.CreateRoom(),
        m.JoinRoom(code="XK42"),
        m.FindMatch(),
        m.ChooseTeam(picks=["Bulbasaur", "Charmander", "Squirtle"]),
        m.SubmitAction(action=m.ActionDTO(kind="fight", index=0)),
        m.SubmitReplace(index=2),
        m.Leave(),
    ]
    for original in originals:
        assert m.parse_client(m.dump(original)) == original


def test_server_messages_round_trip() -> None:
    dto = m.state_to_dto(BattleState(teams=(full_team(), full_team())))
    originals = [
        m.HelloOk(player_id="p1"),
        m.RoomCreated(code="XK42"),
        m.MatchFound(opponent="Bo", your_slot=1),
        m.AwaitLead(),
        m.BattleStart(state=dto),
        m.AwaitAction(turn=3),
        m.AwaitReplacement(),
        m.BattleEnd(winner_slot=0),
        m.OpponentDisconnected(),
        m.ServerError(code="bad", message="nope"),
    ]
    for original in originals:
        assert m.parse_server(m.dump(original)) == original


def test_state_round_trip() -> None:
    state = BattleState(teams=(full_team(lead="Charmander"), full_team(lead="Squirtle")))
    state.team(0).active.current_hp = 17
    rebuilt = m.state_from_dto(m.state_to_dto(state))
    assert rebuilt.team(0).active.name == "Charmander"
    assert rebuilt.team(0).active.current_hp == 17
    assert rebuilt.team(1).active_index == state.team(1).active_index


def test_action_round_trip() -> None:
    for action in (Fight(2), Switch(1), Run()):
        assert m.action_from_dto(m.action_to_dto(action)) == action


def test_events_round_trip_through_a_turn() -> None:
    state = BattleState(teams=(full_team(), full_team()))
    events = resolve_turn(state, (Fight(0), Fight(0)), random.Random(1))
    message = m.TurnResolved(
        events=[m.event_to_dict(event) for event in events], state=m.state_to_dto(state)
    )
    parsed = m.parse_server(m.dump(message))
    assert isinstance(parsed, m.TurnResolved)
    assert [m.event_from_dict(data) for data in parsed.events] == events


def test_parse_client_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        m.parse_client('{"type": "not_a_real_message"}')


def test_event_from_dict_is_hardened_against_hostile_frames() -> None:
    from climon.engine import events as ev

    # An unknown event kind raises a clean ValueError (not a KeyError on a missing class).
    with pytest.raises(ValueError, match="unknown event"):
        m.event_from_dict({"kind": "Evil", "slot": 0})
    # Unexpected fields are dropped instead of passed into the dataclass constructor.
    event = m.event_from_dict({"kind": "Fainted", "slot": 1, "pokemon": "Gengar", "x": "y"})
    assert event == ev.Fainted(slot=1, pokemon="Gengar")


def test_player_name_length_is_bounded_on_the_wire() -> None:
    with pytest.raises(ValidationError):
        m.parse_client('{"type": "hello", "name": "' + "x" * 200 + '"}')
