"""The interactive battle screen.

The player types commands on the command line. Typing an umbrella command (fight,
bag, pokemon, run) shows the options and turns the command boxes into them; pick by
number or name, or type 'back' to return. Every command is case-insensitive. The
turn resolves through the session and events play out in the message log while the
HP bars and party balls update. A two-column scene keeps the classic corners.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, RichLog

from climon.config import get_settings
from climon.engine.actions import Action, Fight, Run, Switch, UseItem
from climon.engine.events import (
    BattleEnded,
    DamageDealt,
    Event,
    Fainted,
    ItemUsed,
    Missed,
    MoveUsed,
    RunAttempted,
    StatChanged,
    SwitchedIn,
)
from climon.engine.items import ITEM_ORDER, ITEMS, Item
from climon.engine.models import BattleState, Category, Move, Pokemon, Team
from climon.engine.resolver import needs_replacement
from climon.engine.types_chart import effectiveness
from climon.transport.base import BattleSession
from climon.tui.command_line import match_member, match_move, parse_command
from climon.tui.screens.resize_guard import ResizeGuard, big_enough
from climon.tui.widgets.commandgrid import CommandGrid
from climon.tui.widgets.hpbar import HPBar
from climon.tui.widgets.infobox import InfoBox
from climon.tui.widgets.partyballs import PartyBalls
from climon.tui.widgets.sprite import SpritePanel

_EFFECT_TEXT = {
    "lower_attack": "lowers the foe's Attack",
    "lower_defense": "lowers the foe's Defense",
}


def _alive(team: Team) -> list[bool]:
    return [not member.is_fainted for member in team.members]


def _move_detail(move: Move) -> str:
    if move.category is Category.STATUS:
        return f"{move.type.value}, {_EFFECT_TEXT.get(move.effect or '', 'status move')}"
    return f"{move.type.value}, power {move.power}"


def _type_str(pokemon: Pokemon) -> str:
    return " / ".join(part.value for part in pokemon.species.types)


def _effect_text(multiplier: float) -> str:
    """A colored verdict for a damage multiplier."""
    if multiplier == 0:
        return "[red]no effect[/]"
    if multiplier >= 2:
        return "[green]super effective[/]"
    if multiplier < 1:
        return "[yellow]not very effective[/]"
    return "neutral"


def match_end_text(reason: str, winner_slot: int, my_slot: int, *, fled: bool) -> str:
    """The single end-of-battle line, covering KO, forfeit, timeout, and a dropped link.

    ``reason`` comes from the session (online: 'opponent_left' / 'timeout' /
    'connection_lost'; local or a normal KO: 'ko'). Keeps the win/lose/draw verdict but
    adds why, so the player always knows what just happened.
    """
    if reason == "connection_lost":
        return "[b red]Lost connection to the server.[/]  [dim]The battle can't continue.[/]"
    if fled:
        return ""  # 'Got away safely!' already explained the exit
    if winner_slot < 0:
        return "[b yellow]It's a draw![/]"
    won = winner_slot == my_slot
    if reason == "opponent_left":
        lead = "[dim]Your opponent left.[/]  "
    elif reason == "timeout":
        timed_out = "Your opponent ran out of time." if won else "You ran out of time."
        lead = f"[dim]{timed_out}[/]  "
    else:
        lead = ""
    return lead + ("[b green]You win![/]" if won else "[b red]You lose...[/]")


class BattleScreen(Screen[None]):
    """A playable battle. The player types commands; the computer answers."""

    MESSAGE_DELAY: ClassVar[float] = 0.45
    BINDINGS: ClassVar[list[BindingType]] = [("ctrl+q", "leave", "Quit")]

    def __init__(self, session: BattleSession) -> None:
        self._session = session
        self._mode = "main"
        self._busy = False
        self._awaiting_replacement = False
        self._over = False
        self._fled = False
        self._pending_item = ""
        self._reduce_motion = get_settings().reduce_motion
        super().__init__()

    def compose(self) -> ComposeResult:
        me = self._session.player_slot
        player = self._state().team(me).active
        enemy = self._state().team(1 - me).active
        with Vertical(id="battle-root"):
            with Horizontal(id="scene"):
                with Vertical(id="left-col"):
                    yield InfoBox(
                        enemy.name,
                        enemy.level,
                        enemy.current_hp,
                        enemy.max_hp,
                        _alive(self._state().team(1 - me)),
                        id="enemy-info",
                    )
                    yield SpritePanel(player.species.sprite_key, "back", id="player-sprite")
                with Vertical(id="right-col"):
                    yield SpritePanel(enemy.species.sprite_key, "front", id="enemy-sprite")
                    yield InfoBox(
                        player.name,
                        player.level,
                        player.current_hp,
                        player.max_hp,
                        _alive(self._state().team(me)),
                        id="player-info",
                    )
            with Horizontal(id="bottom-band"):
                # min_width defaults to 78; the message box is narrower, so without this
                # long lines render past the edge and get clipped instead of wrapping.
                yield RichLog(id="message-log", markup=True, wrap=True, min_width=16)
                yield CommandGrid(id="command-grid")
            yield Input(placeholder="fight / pokemon / bag / run / type / help", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self._prompt()
        self.query_one("#command-input", Input).focus()
        self.call_after_refresh(self._check_size)

    def on_resize(self) -> None:
        self._check_size()

    def _check_size(self) -> None:
        too_small = not big_enough(self.size.width, self.size.height)
        if too_small and not isinstance(self.app.screen, ResizeGuard):
            self.app.push_screen(ResizeGuard())

    async def action_leave(self) -> None:
        """Close the session (so an online opponent is told at once) and quit."""
        await self._session.close()
        self.app.exit()

    # -- input routing -------------------------------------------------------

    @on(Input.Submitted, "#command-input")
    async def _on_submit(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text or self._over:
            return
        low = text.lower()
        if low in ("quit", "exit"):
            await self.action_leave()
            return
        if low in ("help", "?") or low.startswith("help "):
            self._show_help(low)
            return
        if low in ("type", "types", "matchup", "scout"):
            self._show_matchup()
            return
        if self._awaiting_replacement:
            await self._handle_replacement(text)
            return
        if self._busy:
            return
        if low == "back":
            self._to_main()
            return
        if self._mode == "fight":
            await self._handle_fight(text)
        elif self._mode == "pokemon":
            await self._handle_pokemon(text)
        elif self._mode == "bag":
            await self._handle_bag(text)
        elif self._mode == "bag_target":
            await self._handle_bag_target(text)
        elif self._mode == "run_confirm":
            await self._handle_run_confirm(low)
        else:
            await self._handle_main(text, low)

    async def _handle_main(self, text: str, low: str) -> None:
        if low in ("fight", "f"):
            self._enter_fight()
        elif low in ("bag", "b", "item", "items"):
            self._enter_bag()
        elif low in ("pokemon", "pokémon", "poke", "p", "team"):
            self._enter_pokemon()
        elif low in ("run", "flee", "r"):
            self._enter_run_confirm()
        else:
            action = parse_command(text, self._active())
            if action is None:
                self._log("[dim]I don't understand that. Type 'help'.[/]")
            else:
                await self._take_turn(action)

    async def _handle_fight(self, text: str) -> None:
        index = match_move(text, self._active())
        if index is None:
            self._log("[dim]No such move. Type a number, a name, or 'back'.[/]")
            return
        await self._take_turn(Fight(index))

    async def _handle_pokemon(self, text: str) -> None:
        team = self._team()
        index = match_member(text, team)
        if index is None:
            self._log("[dim]No such Pokemon. Type a number, a name, or 'back'.[/]")
        elif team.members[index].is_fainted:
            self._log("[dim]That Pokemon has fainted.[/]")
        elif index == team.active_index:
            self._log("[dim]That Pokemon is already out.[/]")
        else:
            await self._take_turn(Switch(index))

    async def _handle_run_confirm(self, low: str) -> None:
        if low in ("yes", "y"):
            await self._take_turn(Run())
        elif low in ("no", "n"):
            self._to_main()
        else:
            self._log("[dim]Type 'yes' to flee, or 'back' to cancel.[/]")

    async def _handle_bag(self, text: str) -> None:
        items = self._bag_items()
        index = self._match_item(text, items)
        if index is None:
            self._log("[dim]No such item. Type a number, a name, or 'back'.[/]")
            return
        name = items[index][0]
        item = ITEMS[name]
        if item.boost is not None:
            await self._take_turn(UseItem(name, self._team().active_index))
        else:
            self._pending_item = name
            self._enter_bag_target(item)

    async def _handle_bag_target(self, text: str) -> None:
        team = self._team()
        index = match_member(text, team)
        if index is None:
            self._log("[dim]Type the number of a Pokemon, or 'back'.[/]")
            return
        item = ITEMS[self._pending_item]
        target = team.members[index]
        if item.revive and not target.is_fainted:
            self._log("[dim]Use a Revive on a fainted Pokemon.[/]")
        elif not item.revive and target.is_fainted:
            self._log("[dim]That Pokemon has fainted. Use a Revive.[/]")
        elif not item.revive and target.current_hp >= target.max_hp:
            self._log("[dim]That Pokemon already has full HP.[/]")
        else:
            await self._take_turn(UseItem(self._pending_item, index))

    def _enter_bag_target(self, item: Item) -> None:
        team = self._team()
        if item.revive:
            valid = [i for i, m in enumerate(team.members) if m.is_fainted]
            verb = "Revive"
        else:
            valid = [
                i
                for i, m in enumerate(team.members)
                if not m.is_fainted and m.current_hp < m.max_hp
            ]
            verb = "Heal"
        if not valid:
            self._log(f"[dim]No Pokemon to use {self._pending_item} on. Pick another item.[/]")
            return
        self._mode = "bag_target"
        self._grid().set_options([f"{i + 1} {team.members[i].name}" for i in valid])
        self._log(f"[b]{verb} with {self._pending_item}[/]  [dim](or 'back')[/]")
        for i in valid:
            member = team.members[i]
            self._log(
                f"  [b]{i + 1}[/] {member.name}  [dim]({member.current_hp}/{member.max_hp})[/]"
            )

    def _bag_items(self) -> list[tuple[str, int]]:
        bag = self._team().bag
        return [(name, bag[name]) for name in ITEM_ORDER if bag.get(name, 0) > 0]

    def _match_item(self, text: str, items: list[tuple[str, int]]) -> int | None:
        if text.isdigit():
            index = int(text) - 1
            return index if 0 <= index < len(items) else None
        low = text.lower()
        for index, (name, _) in enumerate(items):
            if low and (name.lower().startswith(low) or low in name.lower()):
                return index
        return None

    async def _handle_replacement(self, text: str) -> None:
        team = self._team()
        index = match_member(text, team)
        if index is None or index not in team.live_indices() or index == team.active_index:
            self._log("[dim]Type the number of a healthy Pokemon.[/]")
            return
        await self._play_events(await self._session.replace(index))
        self._awaiting_replacement = False
        if self._over:
            self._finish()
        else:
            self._end_turn()

    # -- submenus ------------------------------------------------------------

    def _enter_fight(self) -> None:
        self._mode = "fight"
        moves = self._active().species.moves
        self._grid().set_options([f"{i + 1} {m.name}" for i, m in enumerate(moves)])
        self._log("[b]Choose a move[/]  [dim](or 'back')[/]")
        for i, m in enumerate(moves):
            self._log(f"  [b]{i + 1}[/] {m.name}  [dim]({m.type.value})[/]")

    def _enter_pokemon(self) -> None:
        self._mode = "pokemon"
        members = self._team().members
        self._grid().set_options([f"{i + 1} {m.name}" for i, m in enumerate(members)])
        self._log("[b]Switch to[/]  [dim](or 'back')[/]")
        for i, m in enumerate(members):
            self._log(f"  [b]{i + 1}[/] {m.name}  [dim]({m.current_hp}/{m.max_hp})[/]")

    def _enter_bag(self) -> None:
        self._mode = "bag"
        items = self._bag_items()
        if not items:
            self._grid().set_options(["(empty)"])
            self._log("Your bag is empty.  [dim](type 'back')[/]")
            return
        self._grid().set_options([f"{i + 1} {name}" for i, (name, _) in enumerate(items)])
        self._log("[b]Use an item[/]  [dim](or 'back')[/]")
        # Two columns so all six items fit without scrolling, but fall back to one
        # column on a narrow box so nothing wraps. Pad by the plain-text width
        # (markup is invisible) so the columns line up.
        plain = [f"{i + 1} {name} x{count}" for i, (name, count) in enumerate(items)]
        markup = [f"[b]{i + 1}[/] {name} [dim]x{count}[/]" for i, (name, count) in enumerate(items)]
        column = max(len(text) for text in plain)
        avail = self.query_one("#message-log", RichLog).size.width
        if avail >= 2 * column + 5:
            for row in range(0, len(plain), 2):
                cells = [
                    markup[col] + " " * (column + 2 - len(plain[col]))
                    for col in range(row, row + 2)
                    if col < len(plain)
                ]
                self._log("  " + "".join(cells))
        else:
            for index in range(len(plain)):
                self._log(f"  {markup[index]}")

    def _enter_run_confirm(self) -> None:
        self._mode = "run_confirm"
        self._grid().set_options(["YES", "NO"])
        self._log("Flee the battle?  Type [b]yes[/]  [dim](or 'back' to cancel)[/]")

    def _to_main(self) -> None:
        self._mode = "main"
        self._grid().reset()
        self._prompt()

    # -- turn flow -----------------------------------------------------------

    async def _take_turn(self, action: Action) -> None:
        self._busy = True
        self._set_input_enabled(enabled=False)
        await self._play_events(await self._session.submit(action))
        if self._over:
            self._finish()
        elif self._session.player_slot in needs_replacement(self._state()):
            self._begin_replacement()
        else:
            self._end_turn()

    def _end_turn(self) -> None:
        self._busy = False
        self._mode = "main"
        self._grid().reset()
        self._set_input_enabled(enabled=True)
        self._prompt()

    def _begin_replacement(self) -> None:
        self._awaiting_replacement = True
        team = self._team()
        live = team.live_indices()
        self._grid().set_options([f"{i + 1} {team.members[i].name}" for i in live])
        self._log("[b]Choose your next Pokemon:[/]")
        for i in live:
            self._log(f"  [b]{i + 1}[/] {team.members[i].name}")
        self._set_input_enabled(enabled=True)

    def _finish(self) -> None:
        self._busy = True
        self._log("[dim]Type 'quit' or press ctrl+q to leave.[/]")
        self._set_input_enabled(enabled=False)

    # -- rendering -----------------------------------------------------------

    async def _play_events(self, events: list[Event]) -> None:
        for event in events:
            self._apply(event)
            message = self._describe(event)
            if message:
                self._log(message)
            if isinstance(event, Fainted):
                self.app.bell()
            await asyncio.sleep(self.MESSAGE_DELAY)

    def _apply(self, event: Event) -> None:
        if isinstance(event, DamageDealt):
            self._refresh(event.slot)
            if not self._reduce_motion:
                self._sprite(event.slot).flash()
        elif isinstance(event, Fainted | SwitchedIn | ItemUsed):
            self._refresh(event.slot)
        elif isinstance(event, RunAttempted) and event.slot == self._session.player_slot:
            self._fled = True
            self._over = True
        elif isinstance(event, BattleEnded):
            self._over = True

    def _refresh(self, slot: int) -> None:
        team = self._state().team(slot)
        active = team.active
        info = self.query_one(f"#{self._slot_name(slot)}-info", InfoBox)
        info.query_one(HPBar).set_hp(
            active.current_hp, active.max_hp, animate=not self._reduce_motion
        )
        info.query_one(PartyBalls).set_alive(_alive(team))
        info.query_one(".info-name", Label).update(f"{active.name}  [dim]Lv{active.level}[/]")
        view = "back" if slot == self._session.player_slot else "front"
        self._sprite(slot).set_pokemon(active.species.sprite_key, view)

    def _describe(self, event: Event) -> str:
        if isinstance(event, MoveUsed):
            return f"{event.pokemon} used [b]{event.move}[/]!"
        if isinstance(event, Missed):
            return f"{event.pokemon}'s attack missed!"
        if isinstance(event, DamageDealt):
            notes = []
            if event.critical:
                notes.append("A critical hit!")
            if event.effectiveness > 1:
                notes.append("It's super effective!")
            elif 0 < event.effectiveness < 1:
                notes.append("It's not very effective...")
            return " ".join(notes)
        if isinstance(event, StatChanged):
            return f"{event.pokemon}'s {event.stat} fell!"
        if isinstance(event, Fainted):
            return f"[b]{event.pokemon}[/] fainted!"
        if isinstance(event, SwitchedIn):
            return f"{event.pokemon} was sent out!"
        if isinstance(event, ItemUsed):
            return f"Used [b]{event.item}[/]!  {event.target} {event.detail}"
        if isinstance(event, RunAttempted):
            return "Got away safely!"
        if isinstance(event, BattleEnded):
            reason = getattr(self._session, "end_reason", "ko")
            return match_end_text(reason, event.winner, self._session.player_slot, fled=self._fled)
        return ""

    # -- help ----------------------------------------------------------------

    def _show_help(self, low: str) -> None:
        arg = low[5:].strip() if low.startswith("help ") else ""
        active = self._active()
        if arg in ("moves", "move", "fight", active.name.lower()):
            self._show_move_help(active)
            return
        self._log("[b]Commands[/]")
        self._log("[b]FIGHT[/] - choose a move to attack")
        self._log("[b]BAG[/] - use an item (Potion, Revive, X Attack, ...)")
        self._log("[b]POKEMON[/] - switch to another team member")
        self._log("[b]RUN[/] - flee the battle (asks to confirm)")
        self._log("[b]TYPE[/] - both Pokemon's types and how every move matches up")
        self._log("[dim]Anywhere: help, help moves, type, back, a number to pick, quit (ctrl+q)[/]")
        self._log(f"[dim]Type 'help moves' to see {active.name}'s moves and PP.[/]")

    def _show_move_help(self, active: Pokemon) -> None:
        self._log(f"[b]{active.name}'s moves[/]")
        for i, move in enumerate(active.species.moves):
            pp = active.pp.get(move.name, move.max_pp)
            self._log(f"[b]{i + 1} {move.name}[/] - {_move_detail(move)}, PP {pp}/{move.max_pp}")

    def _show_matchup(self) -> None:
        me = self._session.player_slot
        mine = self._state().team(me).active
        foe = self._state().team(1 - me).active
        self._log("[b]Type matchup[/]")
        self._log(f"You: [b]{mine.name}[/]  [dim]{_type_str(mine)}[/]")
        self._log(f"Foe: [b]{foe.name}[/]  [dim]{_type_str(foe)}[/]")
        self._log(f"[b]{mine.name}'s moves[/] vs {foe.name}:")
        for move in mine.species.moves:
            self._log("  " + self._matchup_line(move, foe))
        self._log(f"[b]{foe.name}'s moves[/] vs {mine.name}:")
        for move in foe.species.moves:
            self._log("  " + self._matchup_line(move, mine))

    def _matchup_line(self, move: Move, defender: Pokemon) -> str:
        if move.category is Category.STATUS:
            return f"{move.name}  [dim]{move.type.value}, status[/]"
        multiplier = effectiveness(move.type, defender.species.types)
        return (
            f"{move.name}  [dim]{move.type.value}[/]  "
            f"{_effect_text(multiplier)} [dim](x{multiplier:g})[/]"
        )

    # -- helpers -------------------------------------------------------------

    def _state(self) -> BattleState:
        return self._session.state

    def _team(self) -> Team:
        return self._state().team(self._session.player_slot)

    def _active(self) -> Pokemon:
        return self._team().active

    def _grid(self) -> CommandGrid:
        return self.query_one("#command-grid", CommandGrid)

    def _slot_name(self, slot: int) -> str:
        return "player" if slot == self._session.player_slot else "enemy"

    def _sprite(self, slot: int) -> SpritePanel:
        return self.query_one(f"#{self._slot_name(slot)}-sprite", SpritePanel)

    def _prompt(self) -> None:
        active = self._active()
        moves = "  ".join(f"[b]{i + 1}[/] {m.name}" for i, m in enumerate(active.species.moves))
        self._log(
            f"What will [b]{active.name}[/] do?  [dim](fight / pokemon / bag / run / type)[/]"
        )
        self._log(f"[dim]Moves: {moves}[/]")

    def _log(self, message: str) -> None:
        self.query_one("#message-log", RichLog).write(message)

    def _set_input_enabled(self, *, enabled: bool) -> None:
        command_input = self.query_one("#command-input", Input)
        command_input.disabled = not enabled
        if enabled:
            command_input.focus()
