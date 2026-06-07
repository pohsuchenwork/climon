"""Integration test: two real WebSocket clients play a server-resolved turn."""

from __future__ import annotations

import asyncio
import socket

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.server import serve

from climon.protocol import messages as wire
from climon.server.app import Match, Server, _health_check

_STARTERS = ["Bulbasaur", "Charmander", "Squirtle"]


async def _draft_and_await(a: ClientConnection, b: ClientConnection) -> None:
    """From a paired room, both draft the starters and reach AwaitAction."""
    for ws in (a, b):
        await ws.send(wire.dump(wire.ChooseTeam(picks=_STARTERS)))
    for ws in (a, b):
        assert isinstance(await _recv(ws), wire.BattleStart)
        assert isinstance(await _recv(ws), wire.AwaitAction)


def _free_port() -> int:
    probe = socket.socket()
    probe.bind(("localhost", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    return port


async def _recv(ws: ClientConnection) -> wire.ServerMessage:
    return wire.parse_server(await ws.recv())


async def _hello(ws: ClientConnection, name: str) -> None:
    await ws.send(wire.dump(wire.Hello(name=name)))
    assert isinstance(await _recv(ws), wire.HelloOk)


async def _pair_by_room(a: ClientConnection, b: ClientConnection) -> None:
    """Hello on both, create a room on a, join from b, then consume MatchFound + AwaitLead."""
    await _hello(a, "A")
    await _hello(b, "B")
    await a.send(wire.dump(wire.CreateRoom()))
    created = await _recv(a)
    assert isinstance(created, wire.RoomCreated)
    await b.send(wire.dump(wire.JoinRoom(code=created.code)))
    for ws in (a, b):
        assert isinstance(await _recv(ws), wire.MatchFound)
        assert isinstance(await _recv(ws), wire.AwaitLead)


async def test_two_clients_play_a_server_resolved_turn() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await a.send(wire.dump(wire.Hello(name="A")))
            await b.send(wire.dump(wire.Hello(name="B")))
            assert isinstance(await _recv(a), wire.HelloOk)
            assert isinstance(await _recv(b), wire.HelloOk)

            await a.send(wire.dump(wire.CreateRoom()))
            created = await _recv(a)
            assert isinstance(created, wire.RoomCreated)
            await b.send(wire.dump(wire.JoinRoom(code=created.code)))

            assert isinstance(await _recv(a), wire.MatchFound)
            assert isinstance(await _recv(a), wire.AwaitLead)
            assert isinstance(await _recv(b), wire.MatchFound)
            assert isinstance(await _recv(b), wire.AwaitLead)

            await a.send(wire.dump(wire.ChooseTeam(picks=["Bulbasaur", "Charmander", "Squirtle"])))
            await b.send(wire.dump(wire.ChooseTeam(picks=["Bulbasaur", "Charmander", "Squirtle"])))
            assert isinstance(await _recv(a), wire.BattleStart)
            assert isinstance(await _recv(a), wire.AwaitAction)
            assert isinstance(await _recv(b), wire.BattleStart)
            assert isinstance(await _recv(b), wire.AwaitAction)

            fight = wire.SubmitAction(action=wire.ActionDTO(kind="fight", index=0))
            await a.send(wire.dump(fight))
            await b.send(wire.dump(fight))
            resolved = await _recv(a)
            assert isinstance(resolved, wire.TurnResolved)
            assert resolved.state.turn == 1


async def test_quick_match_pairs_two_waiting_clients() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _hello(a, "A")
            await _hello(b, "B")

            await a.send(wire.dump(wire.FindMatch()))
            await b.send(wire.dump(wire.FindMatch()))

            found_a = await _recv(a)
            found_b = await _recv(b)
            assert isinstance(found_a, wire.MatchFound)
            assert isinstance(found_b, wire.MatchFound)
            assert {found_a.your_slot, found_b.your_slot} == {0, 1}
            assert found_a.opponent == "B"
            assert found_b.opponent == "A"
            assert isinstance(await _recv(a), wire.AwaitLead)
            assert isinstance(await _recv(b), wire.AwaitLead)


async def test_illegal_action_is_rejected_and_state_unchanged() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _pair_by_room(a, b)
            await a.send(wire.dump(wire.ChooseTeam(picks=["Bulbasaur", "Charmander", "Squirtle"])))
            await b.send(wire.dump(wire.ChooseTeam(picks=["Bulbasaur", "Charmander", "Squirtle"])))
            for ws in (a, b):
                assert isinstance(await _recv(ws), wire.BattleStart)
                assert isinstance(await _recv(ws), wire.AwaitAction)

            # An out-of-range move index is rejected and does not consume the turn.
            bad = wire.SubmitAction(action=wire.ActionDTO(kind="fight", index=99))
            await a.send(wire.dump(bad))
            error = await _recv(a)
            assert isinstance(error, wire.ServerError)
            assert error.code == "illegal"

            # A legal turn still resolves afterwards, so the state was untouched.
            legal = wire.SubmitAction(action=wire.ActionDTO(kind="fight", index=0))
            await a.send(wire.dump(legal))
            await b.send(wire.dump(legal))
            resolved = await _recv(a)
            assert isinstance(resolved, wire.TurnResolved)
            assert resolved.state.turn == 1


async def test_http_request_gets_a_health_response() -> None:
    # A plain HTTP GET (a platform health probe or a browser) gets 200, not a WS error.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port, process_request=_health_check):
        reader, writer = await asyncio.open_connection("localhost", port)
        writer.write(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        await writer.drain()
        data = await reader.read(1024)
        writer.close()
        await writer.wait_closed()
        assert b"200" in data
        assert b"climon online" in data


async def test_opponent_disconnect_forfeits_the_match() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a:
            b = await connect(url)
            await _pair_by_room(a, b)
            await b.close()

            ended = await _recv(a)
            assert isinstance(ended, wire.BattleEnd)
            assert ended.winner_slot == 0
            assert ended.reason == "opponent_left"


async def test_players_draft_their_own_teams() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _pair_by_room(a, b)
            await a.send(wire.dump(wire.ChooseTeam(picks=["Mewtwo", "Pikachu", "Gengar"])))
            await b.send(wire.dump(wire.ChooseTeam(picks=["Charizard", "Gyarados", "Snorlax"])))
            start = await _recv(a)
            assert isinstance(start, wire.BattleStart)
            host = [member.species for member in start.state.teams[0].members]
            joiner = [member.species for member in start.state.teams[1].members]
            assert host == ["Mewtwo", "Pikachu", "Gengar"]
            assert joiner == ["Charizard", "Gyarados", "Snorlax"]


async def test_invalid_team_draft_is_rejected() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _pair_by_room(a, b)
            await a.send(wire.dump(wire.ChooseTeam(picks=["Pikachu"])))  # too few
            error = await _recv(a)
            assert isinstance(error, wire.ServerError)
            assert error.code == "bad_team"


async def test_redraft_after_a_rejected_team_succeeds() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _pair_by_room(a, b)
            # a sends an over-sized team and is rejected, then re-drafts a valid one.
            too_many = ["Bulbasaur", "Charmander", "Squirtle", "Pikachu"]
            await a.send(wire.dump(wire.ChooseTeam(picks=too_many)))
            error = await _recv(a)
            assert isinstance(error, wire.ServerError)
            assert error.code == "bad_team"
            await a.send(wire.dump(wire.ChooseTeam(picks=_STARTERS)))
            await b.send(wire.dump(wire.ChooseTeam(picks=_STARTERS)))
            for ws in (a, b):
                assert isinstance(await _recv(ws), wire.BattleStart)
                assert isinstance(await _recv(ws), wire.AwaitAction)


async def test_turn_timeout_makes_the_idle_player_lose() -> None:
    original = Match.TURN_SECONDS
    Match.TURN_SECONDS = 0.2
    try:
        server = Server()
        port = _free_port()
        async with serve(server.handler, "localhost", port):
            url = f"ws://localhost:{port}"
            async with connect(url) as a, connect(url) as b:
                await _pair_by_room(a, b)
                await _draft_and_await(a, b)
                # a (slot 0) acts; b (slot 1) stalls past the timer.
                fight = wire.SubmitAction(action=wire.ActionDTO(kind="fight", index=0))
                await a.send(wire.dump(fight))
                ended = await _recv(a)
                assert isinstance(ended, wire.BattleEnd)
                assert ended.winner_slot == 0
                assert ended.reason == "timeout"
    finally:
        Match.TURN_SECONDS = original


async def test_cannot_start_a_second_match_while_in_one() -> None:
    # A player already in a match cannot queue or open a room (would corrupt the opponent's
    # match by overwriting player.match). The lobby commands are ignored.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            await _pair_by_room(a, b)  # a and b are now in a match (choosing phase)
            await a.send(wire.dump(wire.FindMatch()))
            await a.send(wire.dump(wire.CreateRoom()))
            await asyncio.sleep(0.05)
            assert len(server.queue) == 0  # not queued
            assert len(server.rooms) == 0  # no new room


async def test_create_room_keeps_one_room_per_player() -> None:
    # Repeated CreateRoom replaces the player's room instead of leaking unbounded rooms.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a:
            await _hello(a, "A")
            await a.send(wire.dump(wire.CreateRoom()))
            first = await _recv(a)
            await a.send(wire.dump(wire.CreateRoom()))
            second = await _recv(a)
            assert isinstance(first, wire.RoomCreated)
            assert isinstance(second, wire.RoomCreated)
            assert first.code != second.code
            await asyncio.sleep(0.05)
            assert len(server.rooms) == 1  # only the latest, not two


async def test_player_name_is_sanitized() -> None:
    # Control characters are stripped and the name is length-capped before it is shown
    # on the opponent's terminal.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as a, connect(url) as b:
            nasty = "\x1b[31mEVIL\x00" + "A" * 40
            await a.send(wire.dump(wire.Hello(name=nasty)))
            assert isinstance(await _recv(a), wire.HelloOk)
            await _hello(b, "B")
            await a.send(wire.dump(wire.CreateRoom()))
            created = await _recv(a)
            assert isinstance(created, wire.RoomCreated)
            await b.send(wire.dump(wire.JoinRoom(code=created.code)))
            found = await _recv(b)
            assert isinstance(found, wire.MatchFound)
            assert "\x1b" not in found.opponent
            assert "\x00" not in found.opponent
            assert len(found.opponent) <= 24


async def test_turn_timeout_with_both_idle_is_a_draw() -> None:
    original = Match.TURN_SECONDS
    Match.TURN_SECONDS = 0.2
    try:
        server = Server()
        port = _free_port()
        async with serve(server.handler, "localhost", port):
            url = f"ws://localhost:{port}"
            async with connect(url) as a, connect(url) as b:
                await _pair_by_room(a, b)
                await _draft_and_await(a, b)
                # neither acts -> draw (winner_slot -1)
                ended_a = await _recv(a)
                ended_b = await _recv(b)
                assert isinstance(ended_a, wire.BattleEnd) and ended_a.winner_slot == -1
                assert ended_a.reason == "timeout_draw"
                assert isinstance(ended_b, wire.BattleEnd) and ended_b.winner_slot == -1
    finally:
        Match.TURN_SECONDS = original
