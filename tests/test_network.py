"""Integration test: two NetworkSessions play a server-resolved turn on localhost."""

from __future__ import annotations

import asyncio
import socket

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from climon.engine.actions import Fight
from climon.engine.events import BattleEnded
from climon.engine.resolver import needs_replacement
from climon.server.app import Server
from climon.transport import network

_TEAM = ["Bulbasaur", "Charmander", "Squirtle"]


def _free_port() -> int:
    probe = socket.socket()
    probe.bind(("localhost", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    return port


async def test_two_network_sessions_play_a_turn() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as ca, connect(url) as cb:
            await network.hello(ca, "A")
            await network.hello(cb, "B")
            code = await network.create_room(ca)
            await network.join_room(cb, code)
            match_a = await network.await_match(ca)
            match_b = await network.await_match(cb)

            session_a, session_b = await asyncio.gather(
                network.start_battle(ca, match_a.your_slot, _TEAM),
                network.start_battle(cb, match_b.your_slot, _TEAM),
            )
            assert session_a.player_slot != session_b.player_slot

            events_a, _events_b = await asyncio.gather(
                session_a.submit(Fight(0)), session_b.submit(Fight(0))
            )
            assert session_a.state.turn == 1
            assert events_a


async def test_closing_a_session_makes_the_opponent_win() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as ca, connect(url) as cb:
            await network.hello(ca, "A")
            await network.hello(cb, "B")
            code = await network.create_room(ca)
            await network.join_room(cb, code)
            match_a = await network.await_match(ca)
            match_b = await network.await_match(cb)
            session_a, session_b = await asyncio.gather(
                network.start_battle(ca, match_a.your_slot, _TEAM),
                network.start_battle(cb, match_b.your_slot, _TEAM),
            )
            await session_b.close()  # B leaves
            events = await session_a.submit(Fight(0))
            assert session_a.is_over
            assert session_a.end_reason == "opponent_left"
            assert any(
                isinstance(event, BattleEnded) and event.winner == session_a.player_slot
                for event in events
            )


async def test_start_battle_aborts_when_opponent_leaves_before_battle() -> None:
    # The reported bug: after a quick match, the opponent quits during the draft. The
    # client must learn the match is dead (MatchAborted) instead of stalling forever.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as ca:
            cb = await connect(url)
            await network.hello(ca, "A")
            await network.hello(cb, "B")
            code = await network.create_room(ca)
            await network.join_room(cb, code)
            await network.await_match(ca)
            await network.await_match(cb)
            await cb.close()  # B leaves before anyone drafts
            await asyncio.sleep(0.05)  # let the server process the disconnect
            with pytest.raises(network.MatchAborted) as caught:
                await network.start_battle(ca, 0, _TEAM)
            assert caught.value.reason == "opponent_left"


async def test_session_reports_connection_lost_when_link_drops() -> None:
    # A dropped link mid-battle ends the session with feedback, not a crash or a freeze.
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as ca, connect(url) as cb:
            await network.hello(ca, "A")
            await network.hello(cb, "B")
            code = await network.create_room(ca)
            await network.join_room(cb, code)
            match_a = await network.await_match(ca)
            match_b = await network.await_match(cb)
            session_a, _session_b = await asyncio.gather(
                network.start_battle(ca, match_a.your_slot, _TEAM),
                network.start_battle(cb, match_b.your_slot, _TEAM),
            )
            await ca.close()  # A's own link drops
            events = await session_a.submit(Fight(0))
            assert session_a.is_over
            assert session_a.end_reason == "connection_lost"
            assert any(isinstance(event, BattleEnded) for event in events)


async def _play_to_the_end(session: network.NetworkSession) -> None:
    while not session.is_over and session.state.turn < 300:
        slot = session.player_slot
        if slot in needs_replacement(session.state):
            await session.replace(session.state.team(slot).live_indices()[0])
        else:
            await session.submit(Fight(0))


async def test_full_network_battle_reaches_a_winner() -> None:
    server = Server()
    port = _free_port()
    async with serve(server.handler, "localhost", port):
        url = f"ws://localhost:{port}"
        async with connect(url) as ca, connect(url) as cb:
            await network.hello(ca, "A")
            await network.hello(cb, "B")
            code = await network.create_room(ca)
            await network.join_room(cb, code)
            match_a = await network.await_match(ca)
            match_b = await network.await_match(cb)
            session_a, session_b = await asyncio.gather(
                network.start_battle(ca, match_a.your_slot, _TEAM),
                network.start_battle(cb, match_b.your_slot, _TEAM),
            )
            await asyncio.wait_for(
                asyncio.gather(_play_to_the_end(session_a), _play_to_the_end(session_b)),
                timeout=30,
            )
            assert session_a.is_over
            assert session_b.is_over
