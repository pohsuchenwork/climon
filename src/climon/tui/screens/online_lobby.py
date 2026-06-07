"""The online lobby: connect, create or join a room or quick-match, then draft a team."""

from __future__ import annotations

import asyncio
import contextlib
from typing import ClassVar

from pydantic import ValidationError
from rich.markup import escape
from textual import on, work
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Footer, Input, Label
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import WebSocketException

from climon.config import get_settings
from climon.engine.data import ROSTER, TEAM_SIZE
from climon.engine.models import Species
from climon.legal import ONLINE_NOTICE
from climon.protocol import messages as wire
from climon.transport import network
from climon.tui.display import use_ascii
from climon.tui.screens.battle import BattleScreen

_NET_ERRORS = (OSError, ConnectionError, WebSocketException)
# While the player drafts, poll the socket on this cadence so an opponent leaving (or the
# link dropping) is noticed within a fraction of a second without blocking the draft input.
_DRAFT_POLL_SECONDS = 0.4

# Friendly lines for a match that ends before the battle starts, keyed by the server reason.
_PRE_BATTLE_TEXT = {
    "opponent_left": "Your opponent left the match.",
    "timeout": "Your opponent was not ready in time.",
    "timeout_draw": "The match timed out before it began.",
}

_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_SPINNER_ASCII = "|/-\\"
_WAKING_MESSAGES = [
    "Waking up the battle server",
    "The server was taking a nap",
    "Rounding up wild Pokemon",
    "Tightening the Poke Balls",
    "Warming up the arena",
    "Almost there, hang tight",
]
_TRACK_WIDTH = 22


class OnlineLobby(Screen[None]):
    """Connect to the server, find an opponent, draft a team, then battle."""

    BINDINGS: ClassVar[list[BindingType]] = [("ctrl+q", "leave", "Quit")]

    def __init__(self) -> None:
        self._connection: ClientConnection | None = None
        self._slot = 0
        self._phase = "connecting"
        self._opponent = ""
        self._picks: list[str] = []
        self._pending_picks: list[str] | None = None
        self._left = False
        self._status_text = ""
        self._loader: Timer | None = None
        self._loader_frame = 0
        self._loader_messages: list[str] = []
        self._loader_prefix = ""
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="lobby-root"):
            yield Label("c l i m o n  online", id="lobby-logo")
            yield Label("Waking up the server...", id="lobby-status")
            yield Input(placeholder="create  /  join CODE  /  find  /  quit", id="lobby-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#lobby-input", Input).focus()
        self._connect()

    @on(Input.Submitted, "#lobby-input")
    async def _on_input(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        low = text.lower()
        if low in ("quit", "exit"):
            await self.action_leave()
            return
        if self._connection is None:
            return
        if self._phase == "menu":
            self._menu_command(text, low)
        elif self._phase == "choose_team":
            self._draft_command(low)

    async def action_leave(self) -> None:
        """Close the connection (so an opponent waiting on you is freed) and quit."""
        self._left = True
        self._phase = "ended"
        connection, self._connection = self._connection, None
        if connection is not None:
            with contextlib.suppress(OSError, WebSocketException):
                await connection.close()
        self.app.exit()

    def _menu_command(self, text: str, low: str) -> None:
        if low == "create":
            self._create()
        elif low.startswith("join ") and len(text.split()) == 2:
            self._join(text.split()[1].upper())
        elif low in ("find", "quick", "match"):
            self._find()
        else:
            self._status("Type [b]create[/], [b]join CODE[/], or [b]find[/].")

    def _draft_command(self, low: str) -> None:
        if low in ("back", "undo", "cancel"):
            if self._picks:
                removed = self._picks.pop()
                self._show_draft(f"Removed {removed}.")
            else:
                self._show_draft("Nothing to undo.")
            return
        if len(self._picks) >= TEAM_SIZE:
            return  # already have a full team; ignore extra picks
        species = self._match_roster(low)
        if species is None:
            self._show_draft("Pick a number 1-12 or a name.")
        elif species.name in self._picks:
            self._show_draft(f"{species.name} is already on your team.")
        else:
            self._picks.append(species.name)
            if len(self._picks) >= TEAM_SIZE:
                # Hand the team to the draft watcher (the only reader of the socket while
                # drafting) and lock the phase so further input is ignored. The watcher
                # sends it and starts the battle, or reports if the opponent left first.
                self._phase = "starting"
                self._pending_picks = list(self._picks)
                self._status(
                    f"Team set: [b]{', '.join(self._picks)}[/].  Waiting for the opponent..."
                )
            else:
                self._show_draft()

    @work(exclusive=True)
    async def _connect(self) -> None:
        settings = get_settings()
        self._start_loading(_WAKING_MESSAGES)
        connection = await self._dial(settings.server_url)
        self._stop_loading()
        if connection is None:
            self._status("Could not reach the server.  Check your internet, then ctrl+q to quit.")
            return
        self._connection = connection
        try:
            await network.hello(connection, settings.player_name)
        except _NET_ERRORS:
            self._status("The server hiccuped while connecting.  Press ctrl+q and try again.")
            return
        self._phase = "menu"
        self._status(
            "Connected!  Type [b]create[/], [b]join CODE[/], or [b]find[/]."
            "  [dim](online turns have a 60s limit)[/]"
            f"\n[dim]{ONLINE_NOTICE}[/]"
        )

    async def _dial(self, url: str) -> ClientConnection | None:
        # The first attempt waits long enough for a free host to cold-start (the proxy
        # holds the upgrade while the machine boots); later attempts cover a flap.
        for timeout in (75.0, 30.0, 30.0, 20.0):
            try:
                return await connect(url, open_timeout=timeout)
            except _NET_ERRORS:
                await asyncio.sleep(2)
        return None

    @work(exclusive=True)
    async def _create(self) -> None:
        connection = self._connection
        if connection is None:
            return
        self._phase = "waiting"
        try:
            code = await network.create_room(connection)
        except _NET_ERRORS:
            self._connection_lost()
            return
        self._start_loading(
            ["Waiting for an opponent to join", "Send your code to a friend"],
            prefix=f"Your room code: [b]{code}[/]",
        )
        await self._wait_for_match(connection)

    @work(exclusive=True)
    async def _join(self, code: str) -> None:
        connection = self._connection
        if connection is None:
            return
        self._phase = "waiting"
        self._start_loading(["Joining the room", "Linking you up"])
        try:
            await network.join_room(connection, code)
        except _NET_ERRORS:
            self._connection_lost()
            return
        await self._wait_for_match(connection)

    @work(exclusive=True)
    async def _find(self) -> None:
        connection = self._connection
        if connection is None:
            return
        self._phase = "waiting"
        self._start_loading(["Looking for an opponent", "Searching for a challenger"])
        try:
            await network.find_match(connection)
        except _NET_ERRORS:
            self._connection_lost()
            return
        await self._wait_for_match(connection)

    @work(exclusive=True, group="draft")
    async def _watch_draft(self) -> None:
        """Own the socket while the player drafts.

        This is the only reader during the draft, so there is no two-reader race. It
        polls for a server frame (the opponent leaving, or a draft timeout, both of which
        end the match early) and, when the player finishes drafting, sends the team and
        starts the battle. A dropped link reports a lost connection.
        """
        connection = self._connection
        if connection is None:
            return
        while not self._left:
            if self._pending_picks is not None:
                picks, self._pending_picks = self._pending_picks, None
                if await self._send_team_and_begin(connection, picks):
                    return  # battle started, or the match/connection ended
                continue  # the draft was rejected; keep watching while they re-draft
            try:
                raw = await asyncio.wait_for(connection.recv(), _DRAFT_POLL_SECONDS)
            except TimeoutError:
                continue  # no frame yet; loop to re-check for a finished draft
            except _NET_ERRORS:
                if not self._left:
                    self._connection_lost()
                return
            if self._left:
                return
            # Any frame before the battle starts means the match ended early.
            self._return_to_menu(self._frame_text(raw))
            return

    async def _send_team_and_begin(self, connection: ClientConnection, picks: list[str]) -> bool:
        """Send the draft and open the battle. Returns True when the watcher should stop."""
        try:
            session = await network.start_battle(connection, self._slot, picks)
        except network.MatchAborted as aborted:
            self._return_to_menu(_PRE_BATTLE_TEXT.get(aborted.reason, "The match ended."))
            return True
        except ConnectionError as error:
            # The draft was rejected (e.g. a bad team); let the player draft again.
            self._picks = []
            self._phase = "choose_team"
            self._show_draft(f"Could not start: {error}.")
            return False
        except _NET_ERRORS:
            self._connection_lost()
            return True
        self.app.switch_screen(BattleScreen(session))
        return True

    @staticmethod
    def _frame_text(raw: str | bytes) -> str:
        """A user-facing reason for a frame that arrived before the battle started."""
        try:
            message = wire.parse_server(raw)
        except ValidationError:
            return "Lost connection to the server."
        if isinstance(message, wire.BattleEnd):
            return _PRE_BATTLE_TEXT.get(message.reason, "The match ended.")
        if isinstance(message, wire.ServerError):
            return message.message
        return "Your opponent left the match."

    def _return_to_menu(self, note: str) -> None:
        """Leave a dead match/queue with feedback, staying connected so they can replay."""
        self._stop_loading()
        self._pending_picks = None
        self._picks = []
        self._phase = "menu"
        self._status(f"{note}\nType [b]create[/], [b]join CODE[/], or [b]find[/] to play again.")

    def _connection_lost(self) -> None:
        """The link to the server dropped: report it and disconnect."""
        self._stop_loading()
        self._pending_picks = None
        self._phase = "ended"
        self._status("Lost connection to the server.\n[dim]Press ctrl+q to quit.[/]")
        self._drop_connection()

    @work(group="close")
    async def _drop_connection(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            with contextlib.suppress(OSError, WebSocketException):
                await connection.close()

    async def _wait_for_match(self, connection: ClientConnection) -> None:
        try:
            match = await network.await_match(connection)
        except ConnectionError as error:
            # The server refused the request (e.g. no such room): say why and let the
            # player try again, rather than reporting a lost connection.
            self._return_to_menu(str(error))
            return
        except _NET_ERRORS:
            self._connection_lost()
            return
        self._stop_loading()
        self._slot = match.your_slot
        # Escape markup: the opponent name is player-supplied and shown with rich markup.
        self._opponent = escape(match.opponent)
        self._phase = "choose_team"
        self._show_draft()
        self._watch_draft()  # watch for the opponent leaving while we draft

    def _show_draft(self, note: str = "") -> None:
        roster = "  ".join(f"[b]{i + 1}[/] {s.name}" for i, s in enumerate(ROSTER))
        remaining = TEAM_SIZE - len(self._picks)
        chosen = ", ".join(self._picks) if self._picks else "(none yet)"
        prefix = f"{note}  " if note else ""
        self._status(
            f"{prefix}Found [b]{self._opponent}[/]!  Draft your team, lead first "
            f"([b]{remaining}[/] more, or 'back' to undo).\nTeam: [b]{chosen}[/]\n{roster}"
        )

    def _match_roster(self, text: str) -> Species | None:
        if text.isdigit():
            index = int(text) - 1
            return ROSTER[index] if 0 <= index < len(ROSTER) else None
        for species in ROSTER:
            if text and species.name.lower().startswith(text):
                return species
        return None

    # -- loading animation ---------------------------------------------------

    def _start_loading(self, messages: list[str], prefix: str = "") -> None:
        """Animate a spinner and a bouncing Poke Ball with rotating friendly messages."""
        self._stop_loading()
        self._loader_frame = 0
        self._loader_messages = messages
        self._loader_prefix = prefix
        self._loading_tick()
        self._loader = self.set_interval(0.12, self._loading_tick)

    def _stop_loading(self) -> None:
        if self._loader is not None:
            self._loader.stop()
            self._loader = None

    def _loading_tick(self) -> None:
        self._loader_frame += 1
        frame = self._loader_frame
        ascii_only = use_ascii()
        spin = _SPINNER_ASCII if ascii_only else _SPINNER
        spinner = spin[frame % len(spin)]
        messages = self._loader_messages or ["Loading"]
        message = messages[(frame // 18) % len(messages)]
        dots = "." * (1 + (frame // 4) % 3)
        prefix = f"{self._loader_prefix}\n\n" if self._loader_prefix else ""
        self._status(f"{prefix}  {spinner}  [b]{message}[/]{dots}\n\n  {self._ball_track(frame)}")

    def _ball_track(self, frame: int) -> str:
        ball, dot = ("o", ".") if use_ascii() else ("●", "·")
        span = 2 * (_TRACK_WIDTH - 1)
        position = frame % span
        if position >= _TRACK_WIDTH:
            position = span - position
        cells = (
            f"[b yellow]{ball}[/]" if i == position else f"[dim]{dot}[/]"
            for i in range(_TRACK_WIDTH)
        )
        return "".join(cells)

    def _status(self, text: str) -> None:
        self._status_text = text  # kept for tests/inspection; the label renders markup
        self.query_one("#lobby-status", Label).update(text)
