"""Wire protocol for online play: pydantic models plus engine <-> wire conversion.

Every frame is one JSON object with a ``type`` field. Client messages are validated
strictly on the server (untrusted input); server messages carry a render-only public
state and the event stream the client plays out. Each player drafts a team of three
from the roster, so the state carries each member's species name, HP, and active flag.
"""

from __future__ import annotations

import dataclasses
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from climon.engine import events as ev
from climon.engine.actions import Action, Fight, Run, Switch, UseItem
from climon.engine.data import starter_by_name
from climon.engine.models import BattleState, Pokemon, Team

# -- battle state (render-only) ------------------------------------------------


class MemberDTO(BaseModel):
    species: str
    current_hp: int
    max_hp: int


class TeamDTO(BaseModel):
    active: int
    members: list[MemberDTO]
    bag: dict[str, int] = {}


class StateDTO(BaseModel):
    teams: tuple[TeamDTO, TeamDTO]
    turn: int


def state_to_dto(state: BattleState) -> StateDTO:
    return StateDTO(
        teams=(_team_to_dto(state.team(0)), _team_to_dto(state.team(1))), turn=state.turn
    )


def state_from_dto(dto: StateDTO) -> BattleState:
    return BattleState(
        teams=(_team_from_dto(dto.teams[0]), _team_from_dto(dto.teams[1])), turn=dto.turn
    )


def _team_to_dto(team: Team) -> TeamDTO:
    return TeamDTO(
        active=team.active_index,
        members=[
            MemberDTO(species=member.name, current_hp=member.current_hp, max_hp=member.max_hp)
            for member in team.members
        ],
        bag=dict(team.bag),
    )


def _team_from_dto(dto: TeamDTO) -> Team:
    members = []
    for member in dto.members:
        pokemon = Pokemon(species=starter_by_name(member.species))
        pokemon.current_hp = member.current_hp
        members.append(pokemon)
    return Team(members=members, active_index=dto.active, bag=dict(dto.bag))


# -- events --------------------------------------------------------------------

_EVENT_TYPES = {
    cls.__name__: cls
    for cls in (
        ev.MoveUsed,
        ev.Missed,
        ev.DamageDealt,
        ev.StatChanged,
        ev.Fainted,
        ev.SwitchedIn,
        ev.ItemUsed,
        ev.RunAttempted,
        ev.BattleEnded,
    )
}


def event_to_dict(event: ev.Event) -> dict[str, Any]:
    return {"kind": type(event).__name__, **dataclasses.asdict(event)}


def event_from_dict(data: dict[str, Any]) -> ev.Event:
    # Only construct known event types with known fields, so a malformed or hostile
    # server frame raises a clean error here (the caller fails closed) instead of
    # passing unexpected kwargs into a dataclass.
    cls = _EVENT_TYPES.get(str(data.get("kind", "")))
    if cls is None:
        msg = f"unknown event kind: {data.get('kind')!r}"
        raise ValueError(msg)
    allowed = {field.name for field in dataclasses.fields(cls)}
    return cls(**{key: value for key, value in data.items() if key in allowed})


# -- actions -------------------------------------------------------------------


class ActionDTO(BaseModel):
    kind: Literal["fight", "switch", "run", "item"]
    index: int = 0
    item: str = ""


def action_to_dto(action: Action) -> ActionDTO:
    if isinstance(action, Fight):
        return ActionDTO(kind="fight", index=action.move_index)
    if isinstance(action, Switch):
        return ActionDTO(kind="switch", index=action.target_index)
    if isinstance(action, UseItem):
        return ActionDTO(kind="item", index=action.target_index, item=action.item)
    return ActionDTO(kind="run")


def action_from_dto(dto: ActionDTO) -> Action:
    if dto.kind == "fight":
        return Fight(dto.index)
    if dto.kind == "switch":
        return Switch(dto.index)
    if dto.kind == "item":
        return UseItem(item=dto.item, target_index=dto.index)
    return Run()


# -- client -> server ----------------------------------------------------------


class Hello(BaseModel):
    type: Literal["hello"] = "hello"
    name: str = Field(default="Player", max_length=64)


class CreateRoom(BaseModel):
    type: Literal["create_room"] = "create_room"


class JoinRoom(BaseModel):
    type: Literal["join_room"] = "join_room"
    code: str


class FindMatch(BaseModel):
    type: Literal["find_match"] = "find_match"


class ChooseTeam(BaseModel):
    type: Literal["choose_team"] = "choose_team"
    picks: list[str]


class SubmitAction(BaseModel):
    type: Literal["submit_action"] = "submit_action"
    action: ActionDTO


class SubmitReplace(BaseModel):
    type: Literal["submit_replace"] = "submit_replace"
    index: int


class Leave(BaseModel):
    type: Literal["leave"] = "leave"


ClientMessage = Annotated[
    Hello | CreateRoom | JoinRoom | FindMatch | ChooseTeam | SubmitAction | SubmitReplace | Leave,
    Field(discriminator="type"),
]
_CLIENT_ADAPTER: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


# -- server -> client ----------------------------------------------------------


class HelloOk(BaseModel):
    type: Literal["hello_ok"] = "hello_ok"
    player_id: str


class RoomCreated(BaseModel):
    type: Literal["room_created"] = "room_created"
    code: str


class MatchFound(BaseModel):
    type: Literal["match_found"] = "match_found"
    opponent: str
    your_slot: int


class AwaitLead(BaseModel):
    type: Literal["await_lead"] = "await_lead"


class BattleStart(BaseModel):
    type: Literal["battle_start"] = "battle_start"
    state: StateDTO


class AwaitAction(BaseModel):
    type: Literal["await_action"] = "await_action"
    turn: int


class TurnResolved(BaseModel):
    type: Literal["turn_resolved"] = "turn_resolved"
    events: list[dict[str, Any]]
    state: StateDTO


class AwaitReplacement(BaseModel):
    type: Literal["await_replacement"] = "await_replacement"


class BattleEnd(BaseModel):
    type: Literal["battle_end"] = "battle_end"
    winner_slot: int
    reason: str = "ko"


class OpponentDisconnected(BaseModel):
    type: Literal["opponent_disconnected"] = "opponent_disconnected"
    grace_seconds: int = 20


class ServerError(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


ServerMessage = Annotated[
    HelloOk
    | RoomCreated
    | MatchFound
    | AwaitLead
    | BattleStart
    | AwaitAction
    | TurnResolved
    | AwaitReplacement
    | BattleEnd
    | OpponentDisconnected
    | ServerError,
    Field(discriminator="type"),
]
_SERVER_ADAPTER: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)


# -- (de)serialization ---------------------------------------------------------


def dump(message: BaseModel) -> str:
    """Serialize any protocol message to a JSON string."""
    return message.model_dump_json()


def parse_client(raw: str | bytes) -> ClientMessage:
    """Parse and validate an untrusted client message."""
    return _CLIENT_ADAPTER.validate_json(raw)


def parse_server(raw: str | bytes) -> ServerMessage:
    """Parse a server message."""
    return _SERVER_ADAPTER.validate_json(raw)
