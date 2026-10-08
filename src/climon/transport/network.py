"""The online client: NetworkSession plus the handshake helpers the lobby uses.

NetworkSession implements the same BattleSession interface as LocalSession, so the
battle screen does not care whether it is playing the computer or another person. The
server drives the flow, so submit/replace send the action and then consume server
frames until it is this player's turn again (or the battle ends), accumulating the
events to render.
"""

from __future__ import annotations

import contextlib

from pydantic import BaseModel, ValidationError
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import WebSocketException

from climon.engine.actions import Action
from climon.engine.events import BattleEnded, Event
from climon.engine.models import BattleState
from climon.engine.resolver import battle_winner
from climon.protocol import messages as wire

# Errors from decoding an untrusted/hostile server frame. The client treats them as a
# reason to end the battle (fail closed) rather than crash the UI.
_DECODE_ERRORS = (ValidationError, KeyError, ValueError, TypeError)
# Errors from sending to or reading a broken/closed socket. Translated into a clean
# "connection lost" battle end so the UI shows feedback instead of crashing.
_IO_ERRORS = (OSError, WebSocketException)


class MatchAborted(Exception):
    """The match ended before the battle began (the opponent left, or a draft timeout).

    Carries the server's ``reason`` so the lobby can show a fitting message and let the
    player return to the menu instead of being stranded in a dead draft.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class NetworkSession:
    """A battle played against another person through the server."""

    def __init__(self, connection: ClientConnection, player_slot: int, state: BattleState) -> None:
        self._connection = connection
        self._player_slot = player_slot
        self._state = state
        self._over = False
        self._end_reason = "ko"

    @property
    def state(self) -> BattleState:
        return self._state

    @property
    def player_slot(self) -> int:
        return self._player_slot

    @property
    def winner(self) -> int | None:
        return battle_winner(self._state)

    @property
    def is_over(self) -> bool:
        return self._over

    @property
    def end_reason(self) -> str:
        """Why the battle ended: 'ko', 'opponent_left', 'timeout', 'connection_lost'."""
        return self._end_reason

    async def submit(self, action: Action) -> list[Event]:
        try:
            await self._send(wire.SubmitAction(action=wire.action_to_dto(action)))
        except _IO_ERRORS:
            return self._mark_lost([])
        return await self._collect()

    async def replace(self, target_index: int) -> list[Event]:
        try:
            await self._send(wire.SubmitReplace(index=target_index))
        except _IO_ERRORS:
            return self._mark_lost([])
        return await self._collect()

    async def close(self) -> None:
        """Close the connection so the server sees this player leave at once."""
        with contextlib.suppress(*_IO_ERRORS):
            await self._connection.close()

    def _mark_lost(self, events: list[Event]) -> list[Event]:
        """End the battle because the connection dropped, with a feedback event."""
        if not self._over:
            self._over = True
            self._end_reason = "connection_lost"
            events.append(BattleEnded(winner=-1))
        return events

    async def _collect(self) -> list[Event]:
        events: list[Event] = []
        try:
            async for raw in self._connection:
                try:
                    message = wire.parse_server(raw)
                except ValidationError:
                    return self._mark_lost(events)  # a malformed frame ends the battle
                if isinstance(message, wire.TurnResolved):
                    try:
                        new_state = wire.state_from_dto(message.state)
                        new_events = [wire.event_from_dict(data) for data in message.events]
                    except _DECODE_ERRORS:
                        return self._mark_lost(events)
                    self._state = new_state
                    events.extend(new_events)
                    if any(isinstance(event, BattleEnded) for event in events):
                        self._over = True
                        return events
                elif isinstance(message, wire.AwaitAction | wire.AwaitReplacement):
                    return events
                elif isinstance(message, wire.BattleEnd):
                    if not self._over:
                        self._over = True
                        self._end_reason = message.reason
                        events.append(BattleEnded(winner=message.winner_slot))
                    return events
                elif isinstance(message, wire.OpponentDisconnected):
                    continue  # informational; a BattleEnd follows
                elif isinstance(message, wire.ServerError):
                    return events
        except _IO_ERRORS:
            return self._mark_lost(events)
        # The stream ended without a normal battle end -> the connection closed.
        return self._mark_lost(events)

    async def _send(self, message: BaseModel) -> None:
        await self._connection.send(wire.dump(message))


# -- handshake helpers (used by the online lobby) ------------------------------


async def _recv(connection: ClientConnection) -> wire.ServerMessage:
    try:
        message = wire.parse_server(await connection.recv())
    except ValidationError as error:
        raise ConnectionError("malformed server message") from error
    if isinstance(message, wire.ServerError):
        raise ConnectionError(message.message)
    return message


async def hello(connection: ClientConnection, name: str) -> None:
    await connection.send(wire.dump(wire.Hello(name=name)))
    if not isinstance(await _recv(connection), wire.HelloOk):
        raise ConnectionError("handshake failed")


async def create_room(connection: ClientConnection) -> str:
    await connection.send(wire.dump(wire.CreateRoom()))
    message = await _recv(connection)
    if not isinstance(message, wire.RoomCreated):
        raise ConnectionError("expected a room code")
    return message.code


async def join_room(connection: ClientConnection, code: str) -> None:
    await connection.send(wire.dump(wire.JoinRoom(code=code)))


async def find_match(connection: ClientConnection) -> None:
    await connection.send(wire.dump(wire.FindMatch()))


async def await_match(connection: ClientConnection) -> wire.MatchFound:
    message = await _recv(connection)
    if not isinstance(message, wire.MatchFound):
        raise ConnectionError("expected a match")
    if not isinstance(await _recv(connection), wire.AwaitLead):
        raise ConnectionError("expected lead select")
    return message


async def start_battle(connection: ClientConnection, slot: int, picks: list[str]) -> NetworkSession:
    """Send the draft and wait for the battle to start.

    Raises ``MatchAborted`` if the opponent left (or the draft timed out) before the
    battle began, ``ConnectionError`` if the draft was rejected or a frame was malformed,
    and a socket error if the connection dropped. The lobby tells these apart so it can
    return the player to the menu, let them re-draft, or report a lost connection.
    """
    await connection.send(wire.dump(wire.ChooseTeam(picks=picks)))
    started = await _recv(connection)
    if isinstance(started, wire.BattleEnd):
        raise MatchAborted(started.reason)
    if not isinstance(started, wire.BattleStart):
        raise ConnectionError("expected battle start")
    nxt = await _recv(connection)
    if isinstance(nxt, wire.BattleEnd):
        raise MatchAborted(nxt.reason)
    if not isinstance(nxt, wire.AwaitAction):
        raise ConnectionError("expected the first turn")
    try:
        state = wire.state_from_dto(started.state)
    except _DECODE_ERRORS as error:
        raise ConnectionError("malformed battle state") from error
    return NetworkSession(connection, slot, state)
