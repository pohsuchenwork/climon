"""The authoritative online battle server.

One asyncio event loop, no locks. Clients connect over WebSocket, say hello, then
create or join a room by code or find a quick match. Two paired players choose a lead
and play a server-resolved 3v3: the server owns the RNG and runs ``resolve_turn``, so
clients only propose actions and the server validates them (anti-cheat). Run with
``python -m climon.server``.
"""

from __future__ import annotations

import asyncio
import logging
import random
import secrets
from collections import deque
from http import HTTPStatus

from pydantic import BaseModel, ValidationError
from websockets.asyncio.server import ServerConnection, serve
from websockets.http11 import Request, Response

from climon.engine.actions import Action, Fight, Switch, UseItem
from climon.engine.data import TEAM_SIZE, full_team, make_team, species_by_name
from climon.engine.events import BattleEnded, Event
from climon.engine.items import ITEMS
from climon.engine.models import BattleState, Team
from climon.engine.resolver import apply_replacement, needs_replacement, resolve_turn
from climon.protocol import messages as wire

logger = logging.getLogger("climon.server")

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 6  # 31**6 ~= 887M codes: not feasible to guess (was 4 = ~923k)
_MAX_NAME_LENGTH = 24
# A public server must bound resources: cap concurrent connections and the size of a
# single client frame (every legitimate client message is tiny). Guards against memory
# and CPU exhaustion from a flood of connections or oversized payloads.
MAX_CONNECTIONS = 256
MAX_MESSAGE_BYTES = 16 * 1024


def _make_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def _clean_name(name: str) -> str:
    """Bound and sanitize a player-supplied name (printable only, length-capped).

    The name is shown on the opponent's screen, so stripping control characters here
    (and escaping markup at the render site) prevents terminal/markup abuse.
    """
    cleaned = "".join(ch for ch in name if ch.isprintable())[:_MAX_NAME_LENGTH].strip()
    return cleaned or "Player"


def _valid_picks(picks: list[str]) -> bool:
    """A team draft must be three distinct, known roster Pokemon."""
    if len(picks) != TEAM_SIZE or len({name.lower() for name in picks}) != TEAM_SIZE:
        return False
    try:
        for name in picks:
            species_by_name(name)
    except KeyError:
        return False
    return True


def _legal_item(team: Team, action: UseItem) -> bool:
    """An item use is legal if it is owned and the target suits the item's effect."""
    item = ITEMS.get(action.item)
    if item is None or team.bag.get(item.name, 0) <= 0:
        return False
    if item.boost is not None:
        return True
    if not 0 <= action.target_index < len(team.members):
        return False
    target = team.members[action.target_index]
    if item.revive:
        return target.is_fainted
    return not target.is_fainted and target.current_hp < target.max_hp


class Player:
    """A connected client: its socket, name, and current match."""

    def __init__(self, connection: ServerConnection) -> None:
        self.connection = connection
        self.id = secrets.token_hex(8)
        self.name = "Player"
        self.match: Match | None = None
        self.slot = 0
        self.room_code: str | None = None  # at most one open room per player

    async def send(self, message: BaseModel) -> None:
        await self.connection.send(wire.dump(message))


class Match:
    """One server-resolved battle between two players."""

    # A player who does not act within this many seconds forfeits the turn; if neither
    # acts it is a draw (see _handle_timeout). Class-level so tests can shorten it.
    TURN_SECONDS: float = 60.0

    def __init__(self, players: tuple[Player, Player], seed: int) -> None:
        self.players = players
        for slot, player in enumerate(players):
            player.match = self
            player.slot = slot
        self.rng = random.Random(seed)
        # Placeholder until both players draft; replaced in choose_team.
        self.state = BattleState(teams=(full_team(), full_team()))
        self._teams: list[Team | None] = [None, None]
        self.actions: dict[int, Action] = {}
        self.replacements: set[int] = set()
        self.phase = "choosing"
        self._timer: asyncio.Task[None] | None = None

    async def start(self) -> None:
        for slot, player in enumerate(self.players):
            await player.send(wire.MatchFound(opponent=self.players[1 - slot].name, your_slot=slot))
            await player.send(wire.AwaitLead())
        self._arm_timer()

    async def choose_team(self, slot: int, picks: list[str]) -> None:
        if self.phase != "choosing" or self._teams[slot] is not None:
            return
        if not _valid_picks(picks):
            await self.players[slot].send(
                wire.ServerError(code="bad_team", message="Pick three different Pokemon.")
            )
            return
        self._teams[slot] = make_team(picks)
        first, second = self._teams
        if first is not None and second is not None:
            self.state = BattleState(teams=(first, second))
            self.phase = "actions"
            await self._broadcast(wire.BattleStart(state=wire.state_to_dto(self.state)))
            await self._await_actions()

    async def submit_action(self, slot: int, dto: wire.ActionDTO) -> None:
        if self.phase != "actions" or slot in self.actions:
            return
        action = wire.action_from_dto(dto)
        if not self._legal(slot, action):
            await self.players[slot].send(wire.ServerError(code="illegal", message="Illegal move."))
            return
        self.actions[slot] = action
        if len(self.actions) == 2:
            await self._resolve()

    async def submit_replace(self, slot: int, index: int) -> None:
        if self.phase != "replacing" or slot not in self.replacements:
            return
        team = self.state.team(slot)
        if index not in team.live_indices() or index == team.active_index:
            await self.players[slot].send(
                wire.ServerError(code="illegal", message="Pick a healthy Pokemon.")
            )
            return
        events = apply_replacement(self.state, slot, index)
        await self._broadcast(self._turn_message(events))
        self.replacements.discard(slot)
        if not self.replacements:
            self.phase = "actions"
            await self._await_actions()

    async def opponent_left(self, leaver_slot: int) -> None:
        if self.phase == "ended":
            return
        self.phase = "ended"
        self._cancel_timer()
        await self.players[1 - leaver_slot].send(
            wire.BattleEnd(winner_slot=1 - leaver_slot, reason="opponent_left")
        )

    # -- per-turn timer ------------------------------------------------------

    def _arm_timer(self) -> None:
        """(Re)start the countdown for the current waiting phase."""
        self._cancel_timer()
        self._timer = asyncio.create_task(self._timeout_guard())

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    async def _timeout_guard(self) -> None:
        try:
            await asyncio.sleep(self.TURN_SECONDS)
        except asyncio.CancelledError:
            return
        await self._handle_timeout()

    async def _handle_timeout(self) -> None:
        """Whoever did not act in time loses; if neither acted it is a draw."""
        if self.phase == "actions":
            missing = [slot for slot in (0, 1) if slot not in self.actions]
        elif self.phase == "replacing":
            missing = sorted(self.replacements)
        elif self.phase == "choosing":
            missing = [slot for slot in (0, 1) if self._teams[slot] is None]
        else:
            return
        self.phase = "ended"
        if len(missing) >= 2:
            await self._broadcast(wire.BattleEnd(winner_slot=-1, reason="timeout_draw"))
        elif len(missing) == 1:
            await self._broadcast(wire.BattleEnd(winner_slot=1 - missing[0], reason="timeout"))

    async def _resolve(self) -> None:
        self.phase = "resolving"
        events = resolve_turn(self.state, (self.actions[0], self.actions[1]), self.rng)
        self.actions = {}
        await self._broadcast(self._turn_message(events))
        ended = next((event for event in events if isinstance(event, BattleEnded)), None)
        if ended is not None:
            self.phase = "ended"
            self._cancel_timer()
            await self._broadcast(wire.BattleEnd(winner_slot=ended.winner))
        elif reps := needs_replacement(self.state):
            self.phase = "replacing"
            self.replacements = set(reps)
            for slot in reps:
                await self.players[slot].send(wire.AwaitReplacement())
            self._arm_timer()
        else:
            self.phase = "actions"
            await self._await_actions()

    async def _await_actions(self) -> None:
        for player in self.players:
            await player.send(wire.AwaitAction(turn=self.state.turn))
        self._arm_timer()

    def _turn_message(self, events: list[Event]) -> wire.TurnResolved:
        return wire.TurnResolved(
            events=[wire.event_to_dict(event) for event in events],
            state=wire.state_to_dto(self.state),
        )

    def _legal(self, slot: int, action: Action) -> bool:
        team = self.state.team(slot)
        if isinstance(action, Fight):
            return 0 <= action.move_index < len(team.active.species.moves)
        if isinstance(action, Switch):
            return action.target_index in team.live_indices() and (
                action.target_index != team.active_index
            )
        if isinstance(action, UseItem):
            return _legal_item(team, action)
        return True

    async def _broadcast(self, message: BaseModel) -> None:
        for player in self.players:
            await player.send(message)


class Server:
    """Tracks connections, rooms, and the matchmaking queue."""

    def __init__(self) -> None:
        self.players: dict[str, Player] = {}
        self.rooms: dict[str, str] = {}
        self.queue: deque[str] = deque()
        self._seed = 0

    async def handler(self, connection: ServerConnection) -> None:
        if len(self.players) >= MAX_CONNECTIONS:
            await connection.close(code=1013, reason="server is at capacity")
            return
        player = Player(connection)
        self.players[player.id] = player
        logger.info("connect %s", player.id)
        try:
            async for raw in connection:
                try:
                    message = wire.parse_client(raw)
                except ValidationError:
                    await player.send(wire.ServerError(code="bad_message", message="Bad message."))
                    continue
                await self._dispatch(player, message)
        finally:
            await self._disconnect(player)

    async def _dispatch(self, player: Player, message: wire.ClientMessage) -> None:
        if isinstance(message, wire.Hello):
            player.name = _clean_name(message.name)
            await player.send(wire.HelloOk(player_id=player.id))
        elif isinstance(message, wire.CreateRoom):
            await self._create_room(player)
        elif isinstance(message, wire.JoinRoom):
            await self._join_room(player, message.code.upper())
        elif isinstance(message, wire.FindMatch):
            await self._find_match(player)
        elif isinstance(message, wire.ChooseTeam) and player.match is not None:
            await player.match.choose_team(player.slot, message.picks)
        elif isinstance(message, wire.SubmitAction) and player.match is not None:
            await player.match.submit_action(player.slot, message.action)
        elif isinstance(message, wire.SubmitReplace) and player.match is not None:
            await player.match.submit_replace(player.slot, message.index)
        elif isinstance(message, wire.Leave):
            await self._disconnect(player)

    @staticmethod
    def _in_active_match(player: Player) -> bool:
        """True if the player is in a match that has not ended yet."""
        return player.match is not None and player.match.phase != "ended"

    def _clear_room(self, player: Player) -> None:
        if player.room_code is not None:
            self.rooms.pop(player.room_code, None)
            player.room_code = None

    async def _create_room(self, player: Player) -> None:
        if self._in_active_match(player):
            return  # cannot open a room while already battling
        self._clear_room(player)  # at most one open room per player bounds memory
        code = _make_code()
        while code in self.rooms:
            code = _make_code()
        self.rooms[code] = player.id
        player.room_code = code
        await player.send(wire.RoomCreated(code=code))

    async def _join_room(self, player: Player, code: str) -> None:
        if self._in_active_match(player):
            return
        host_id = self.rooms.pop(code, None)
        host = self.players.get(host_id) if host_id else None
        if host is None or host is player or self._in_active_match(host):
            if host is player and host_id is not None:
                self.rooms[code] = host_id
            await player.send(wire.ServerError(code="no_room", message="No such room."))
            return
        host.room_code = None
        await Match((host, player), self._next_seed()).start()

    async def _find_match(self, player: Player) -> None:
        if self._in_active_match(player) or player.id in self.queue:
            return  # do not start a second match or queue the same player twice
        while self.queue:
            other = self.players.get(self.queue.popleft())
            if other is not None and other is not player and not self._in_active_match(other):
                await Match((other, player), self._next_seed()).start()
                return
        self.queue.append(player.id)

    async def _disconnect(self, player: Player) -> None:
        if player.id not in self.players:
            return
        del self.players[player.id]
        if player.id in self.queue:
            self.queue.remove(player.id)
        self._clear_room(player)
        if player.match is not None:
            await player.match.opponent_left(player.slot)

    def _next_seed(self) -> int:
        self._seed += 1
        return self._seed


def _health_check(connection: ServerConnection, request: Request) -> Response | None:
    """Answer non-WebSocket requests (host health probes, browser visits) with 200 OK.

    A WebSocket upgrade is let through to the normal handler; anything else (a plain
    GET from a platform health check) gets a short 200 so the service reads as healthy.
    """
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None
    return connection.respond(HTTPStatus.OK, "climon online\n")


async def serve_forever(host: str = "localhost", port: int = 8765) -> None:
    server = Server()
    async with serve(
        server.handler,
        host,
        port,
        process_request=_health_check,
        max_size=MAX_MESSAGE_BYTES,
    ):
        logger.info("climon server listening on ws://%s:%d", host, port)
        await asyncio.Future()
