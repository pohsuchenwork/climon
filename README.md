# CLImon

A terminal Pokemon battle game you play entirely from the command line. Battle the computer,
or another player online, with colorful sprite art and the familiar FIGHT / BAG / POKEMON /
RUN flow.

> **CLImon** is the game; **`climon`** (all lowercase) is the command you type to run it.

> CLImon is an unofficial, non-commercial fan project, not affiliated with or endorsed by
> Nintendo, Creatures, GAME FREAK, or The Pokemon Company. Pokemon, character names, and
> sprite artwork are trademarks and copyrighted works of their owners; all rights are reserved
> to them. Provided AS IS, without warranty. See the attribution note below and `legal/`.

## Warning - please read before installing

CLImon is a free, unofficial fan project provided **AS IS**. By installing or using it, you
accept all three of the following:

1. **No warranty.** CLImon comes with no warranty of any kind. It may not work, may stop
   working, or may behave unexpectedly.
2. **Use at your own risk.** You install and run CLImon entirely at your own risk and are
   responsible for your own computer and data.
3. **No liability.** To the maximum extent permitted by law, the author is not liable for any
   damage, data loss, or harm of any kind arising from installing or using CLImon. If
   something breaks on your machine, that is not the author's responsibility.

The app shows this warning and asks you to accept it the first time you run it. Full notices:
run `climon legal` or see the `legal/` folder.

## Quick start (macOS) - never used a terminal? Start here

You do not need any technical knowledge. Follow these steps exactly. For each step, type (or
paste) the line into the Terminal window and press **Enter**.

**1. Open the Terminal app.**
Press **Cmd + Space** to open Spotlight, type **Terminal**, and press **Enter**. A window with
a text prompt opens - that is where the commands go.

**2. Install uv (this also installs Python for you).**
Paste this whole line and press Enter:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

When it finishes, **close the Terminal window and open a new one** so it picks up the new
program.

**3. Install CLImon.**
Paste this and press Enter:

```
uv tool install git+https://github.com/pohsuchenwork/climon
```

(If a later step ever says `climon: command not found`, run `uv tool update-shell`, then close
and reopen Terminal.)

**4. Start the game.**
Type this and press Enter:

```
climon
```

**5. Accept the one-time notice.**
The first time only, CLImon prints a short warning and asks you to type **`agree`**. Type
`agree`, press Enter, and you are in.

That's it. You'll see the CLImon menu - type `play` to battle the computer, or `online` to
play someone else.

**To update later:** run `uv tool upgrade climon`.

## The menu

Running `climon` opens an interactive menu. Type one of:

- `play` - battle the computer
- `online` - battle another player online
- `legal` - the affiliation and legal notices
- `help` - list the commands
- `quit` - leave

You can also skip the menu and go straight in with `climon play` or `climon online`.

## How to play

First you **draft a team of 3 from 12 Pokemon** (your lead first); the computer or your
opponent drafts its own three. In the draft, type a number (1-12) or a name to pick, or `back`
to undo. Battles are last-Pokemon-standing.

Each turn, type one of these commands, then choose from the options it shows (by number or
name), or type `back` to go back:

- **FIGHT** - choose a move to attack. Type matchups matter (Fire beats Grass, Electric is
  super effective on Water and Flying, and so on), and dual-type weaknesses stack.
- **POKEMON** - switch to another team member (uses your turn; the incoming Pokemon takes the
  next hit).
- **BAG** - use an item: Potion / Super Potion / Hyper Potion and Full Restore heal, Revive
  brings back a fainted teammate, X Attack raises Attack. Using an item takes your turn.
- **RUN** - forfeit the battle.
- **TYPE** - (any time, costs no turn) scout the matchup: both Pokemon's types and how
  effective every move on each side is.

`help` explains everything during a battle. When your active Pokemon faints you send in the
next one for free. Last side standing wins.

## Online play

Type `online` (or run `climon online`). By default CLImon connects to the project's **hosted
server**, so you can play right away with no setup.

In the lobby, type `create` to get a room code to share with a friend, `join CODE` to join
their room, or `find` to be matched with whoever else is waiting. Then draft your team and
battle. Online turns have a **60-second limit** so a game can't be stalled forever: if a
player doesn't move in time they forfeit, and if neither moves it's a draw.

The hosted server is free and sleeps when no one is using it, so the very first connection of
the day takes a few seconds to wake up (CLImon shows a "waking the server" animation). It
stays awake while you play.

Online play is authoritative: the server owns the random seed and resolves every turn, so the
two clients only propose actions and no client can cheat. The sprite art never crosses the
network; only game actions and state do.

### Run your own server (optional)

You can host your own server instead of using the default. Run the server in one terminal,
then point the client at it with the `CLIMON_SERVER` environment variable:

```
uv run python -m climon.server                     # serves ws://localhost:8765
CLIMON_SERVER=ws://localhost:8765 climon online     # connect to your local server
```

To host for others for free, the repo ships a `Dockerfile` and a `render.yaml` Blueprint: push
your fork to GitHub, then in the Render dashboard choose "New +" then "Blueprint" and point it
at the repo. Use the resulting host as `CLIMON_SERVER=wss://your-app.onrender.com`. The same
`Dockerfile` or `python -m climon.server` also runs on an always-on micro VM (Google Compute
Engine or Oracle Cloud free tiers) or behind a free Cloudflare Tunnel.

## Appearance and accessibility

- Theme: set `theme = "light"` (or `"dark"`) in the config, or `CLIMON_THEME=light`.
- Reduce motion: set `reduce_motion = true` to make HP changes instant and skip the hit flash.
- `NO_COLOR`: honored. The block and circle glyphs become ASCII and the terminal's own palette
  is used.
- The battle needs at least an 80x28 terminal; below that a guard pauses play until you resize.

## Development

```
uv sync                       # create the env and install everything
uv run climon --help          # run the CLI
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy                   # types
```

Configuration lives in a TOML file under your XDG config dir (for example
`~/.config/climon/config.toml`). Logs go to the XDG state dir, never to stdout.

## Intellectual property and attribution

CLImon is an unofficial, **non-commercial** fan project. It bundles Pokemon sprite artwork and
uses Pokemon names.

> **Pokemon, the Pokemon character names, and all sprite artwork are trademarks and
> copyrighted works of Nintendo, Creatures Inc., GAME FREAK Inc., and The Pokemon Company. All
> rights in them are reserved to those owners.** CLImon is not affiliated with, endorsed by, or
> sponsored by them, is free and not for sale, and claims no ownership of or rights in their
> property.

Being straight about the law: this attribution is the responsible thing to do, but it does
**not** make distributing those assets lawful and does not remove the risk of a copyright
takedown or claim. Replacing the sprites and names with original or openly licensed assets is
the only way to be fully in the clear. See `legal/DISCLAIMER.md`.

**Rights holders:** if you represent a rights holder and would like CLImon, or any specific
asset, removed, please open an issue on this repository and it will be taken down promptly.

## Legal

Draft legal documents live in the `legal/` folder: Terms of Service, EULA, Privacy Policy, and
Disclaimer. They are **drafts that require review by a licensed attorney** before use, and they
do not cure the intellectual-property issue above. In the app, type `legal` in the menu or run
`climon legal` for the short notices.

## License

CLImon's own source code is licensed under the **MIT License** (see `LICENSE`). The MIT license
covers the code **only** - it does not cover the bundled Pokemon sprite artwork or names, which
belong to their respective owners (see the attribution above and `legal/DISCLAIMER.md`).
