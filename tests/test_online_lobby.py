"""Online lobby integration: the draft watcher reacts when the opponent leaves.

Drives a real lobby app (player A) against a real server, with player B as a raw
WebSocket client. Reproduces the reported bug: B quits during the draft, and A must get
feedback and return to a usable state instead of being stranded.
"""

from __future__ import annotations

import asyncio
import socket

import pytest
from textual.widgets import Input
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from climon.config import get_settings
from climon.protocol import messages as wire
from climon.server.app import Server
from climon.tui.app import ClimonApp
from climon.tui.screens import online_lobby
from climon.tui.screens.online_lobby import OnlineLobby


def _free_port() -> int:
    probe = socket.socket()
    probe.bind(("localhost", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    return port


async def _wait_phase(screen: OnlineLobby, phase: str, timeout: float = 5.0) -> None:
    elapsed = 0.0
    while screen._phase != phase and elapsed < timeout:
        await asyncio.sleep(0.05)
        elapsed += 0.05
    assert screen._phase == phase, f"stuck in {screen._phase!r}, expected {phase!r}"


async def test_opponent_leaving_the_draft_returns_you_to_the_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(online_lobby, "_DRAFT_POLL_SECONDS", 0.05)
    server = Server()
    port = _free_port()
    monkeypatch.setenv("CLIMON_SERVER", f"ws://localhost:{port}")
    get_settings.cache_clear()
    try:
        async with serve(server.handler, "localhost", port):
            # Player B opens a room with a raw client.
            opponent = await connect(f"ws://localhost:{port}")
            await opponent.send(wire.dump(wire.Hello(name="Rival")))
            assert isinstance(wire.parse_server(await opponent.recv()), wire.HelloOk)
            await opponent.send(wire.dump(wire.CreateRoom()))
            created = wire.parse_server(await opponent.recv())
            assert isinstance(created, wire.RoomCreated)

            # Player A is the real lobby app; it auto-connects to the same server.
            app = ClimonApp(online=True)
            async with app.run_test(size=(100, 30)) as pilot:
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, OnlineLobby)
                await _wait_phase(screen, "menu")

                # A joins B's room and reaches the draft.
                lobby_input = screen.query_one("#lobby-input", Input)
                lobby_input.focus()
                lobby_input.value = f"join {created.code}"
                await pilot.press("enter")
                await _wait_phase(screen, "choose_team")

                # B rage-quits mid-draft. A must be told and dropped back to the menu,
                # still connected so they can immediately find another match.
                await opponent.close()
                await _wait_phase(screen, "menu")
                assert "left" in screen._status_text.lower()
                assert screen._connection is not None  # still connected, can replay
    finally:
        get_settings.cache_clear()
