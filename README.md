# climon

A terminal Pokemon battle game with a classic full-screen TUI, played entirely
from the command line. Battle the computer, or another player online, with
chafa-rendered sprites and the familiar FIGHT / BAG / POKEMON / RUN flow.

> climon is an unofficial, non-commercial fan project, not affiliated with or endorsed by
> Nintendo, Creatures, GAME FREAK, or The Pokemon Company. Pokemon, character names, and
> sprite artwork are trademarks and copyrighted works of their owners; all rights are
> reserved to them. Provided AS IS, without warranty. See the attribution note below and
> `legal/`.

## Warning - please read before installing

climon is a free, unofficial fan project provided **AS IS**. By installing or using it,
you accept all three of the following:

1. **No warranty.** climon comes with no warranty of any kind. It may not work, may stop
   working, or may behave unexpectedly.
2. **Use at your own risk.** You install and run climon entirely at your own risk and are
   responsible for your own computer and data.
3. **No liability.** To the maximum extent permitted by law, the author is not liable for
   any damage, data loss, or harm of any kind arising from installing or using climon. If
   something breaks on your machine, that is not the author's responsibility.

The app shows this warning and asks you to accept it the first time you run it. Full
notices: run `climon legal` or see the `legal/` folder.

> Status: playable. Local battles and online play (room codes and quick-match) are done.

## Quick start (macOS)

You need **Python 3.12 or newer** and **[uv](https://docs.astral.sh/uv/)** (a fast Python
package manager). Install uv with:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install and launch climon straight from GitHub:

1. Install it as a global command:
   ```
   uv tool install git+https://github.com/pohsuchenwork/climon
   ```
2. Run it:
   ```
   climon
   ```
3. The **first time** you run climon it shows a short warning (no warranty, use at your own
   risk) and asks you to type **`agree`** and press Enter. After that it opens the menu, where
   you type `play`, `online`, `legal`, `help`, or `quit`.

To update later: `uv tool upgrade climon` (or `uv tool install --force
git+https://github.com/pohsuchenwork/climon`).

## Install (from a checkout)

```
uv sync
uv run climon --help        # run in place
uv tool install .           # or install the global `climon` command
```

The prebuilt sprites are bundled, so you do **not** need anything extra to play. Rebuilding
the sprites from source is optional and needs `chafa` (`brew install chafa`).

## Usage

```
climon              # open the interactive shell (the menu)
climon start        # same as bare climon
climon --help       # list every command
climon play         # battle the computer
climon online       # battle another player online
climon legal        # affiliation and legal notices
```

## Gameplay

You draft a team of **3 from 12 Pokemon** (your lead first); the computer (or your
opponent) drafts its own three. Battles are last-Pokemon-standing:

- **FIGHT** a move - type matchups matter (Fire beats Grass, Electric is super effective
  on Water/Flying, and so on), and dual-type weaknesses stack.
- **POKEMON** to switch (uses your turn; the incoming Pokemon takes the next hit).
- **BAG** to use an item: Potion / Super Potion / Hyper Potion and Full Restore heal,
  Revive brings back a fainted teammate, X Attack raises Attack. Using an item takes your
  turn.
- **RUN** to forfeit.
- **`type`** (any time, no turn used) scouts the matchup: both Pokemon's types and the type
  and effectiveness of every move on each side.

When your active Pokemon faints you send in the next one for free. Last side standing wins.

## Online play

Online mode is authoritative: a small server owns the random seed and resolves
every turn, so the two clients only propose actions (no client can cheat). The
sprite art never crosses the network; only game actions and state do.

Host a server and play on one machine with three terminals:

```
uv run python -m climon.server     # the server on ws://localhost:8765
uv run climon online               # player one
uv run climon online               # player two
```

In the lobby, type `create` to get a room code to share, `join CODE` to join a
friend's room, or `find` to be matched with whoever is waiting. Then draft your
team and battle. Online turns have a **60-second limit** so a game can't be stalled
forever: if a player doesn't move in time they forfeit, and if neither moves it is
a draw. To play across machines, point the client at a remote server:

```
CLIMON_SERVER=wss://climon-server.onrender.com climon online
```

### Hosting the server for free (Render)

The repo ships a `Dockerfile` and a `render.yaml` Blueprint. Push this repo to
GitHub, then in the Render dashboard choose "New +" then "Blueprint" and point it
at the repo. Render reads `render.yaml`, builds the image, and runs the server on
the free plan. Use the resulting host as `CLIMON_SERVER`:

```
CLIMON_SERVER=wss://climon-server.onrender.com climon online
```

A free Render service sleeps after 15 minutes idle and wakes on the next
connection (about a minute); it stays awake during an active battle. The client
shows a "waking the server" message and waits, so the first connect of the day is
just a short pause.

Other forever-free options avoid the cold start: an always-on micro VM on Google
Compute Engine or Oracle Cloud (both have an always-free tier), or self-hosting
behind a free Cloudflare Tunnel. The same `Dockerfile` or `python -m climon.server`
runs on any of them.

## Appearance and accessibility

- Theme: set `theme = "light"` (or `"dark"`) in the config, or `CLIMON_THEME=light`.
- Reduce motion: set `reduce_motion = true` to make HP changes instant and skip the
  hit flash.
- `NO_COLOR`: honored. The block and circle glyphs become ASCII and the terminal's
  own palette is used.
- The battle needs at least an 80x28 terminal; below that a guard pauses play until
  you resize.

## Demo

To record a terminal cast of a battle:

```
asciinema rec climon.cast       # play a battle, then exit to stop
agg climon.cast climon.gif      # optional: turn the cast into a GIF
```

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

climon is an unofficial, **non-commercial** fan project. It bundles Pokemon sprite artwork
and uses Pokemon names.

> **Pokemon, the Pokemon character names, and all sprite artwork are trademarks and
> copyrighted works of Nintendo, Creatures Inc., GAME FREAK Inc., and The Pokemon Company.
> All rights in them are reserved to those owners.** climon is not affiliated with, endorsed
> by, or sponsored by them, is free and not for sale, and claims no ownership of or rights in
> their property.

Being straight about the law: this attribution is the responsible thing to do, but it does
**not** make distributing those assets lawful and does not remove the risk of a copyright
takedown or claim. Replacing the sprites and names with original or openly licensed assets is
the only way to be fully in the clear. See `legal/DISCLAIMER.md`.

**Rights holders:** if you represent a rights holder and would like climon, or any specific
asset, removed, please open an issue on this repository and it will be taken down promptly.

## Legal

Draft legal documents live in the `legal/` folder: Terms of Service, EULA, Privacy Policy,
and Disclaimer. They are **drafts that require review by a licensed attorney** before use,
and they do not cure the intellectual-property issue above. In the app, type `legal` in the
shell or run `climon legal` for the short notices. The software license is MIT (see below).

## License

climon's original source code is licensed under the **MIT License** (see `LICENSE`). The MIT
License covers the code **only** - it does **not** cover the bundled Pokemon sprite artwork or
names, which belong to their respective owners (see the attribution above and
`legal/DISCLAIMER.md`). Third-party dependency licenses are listed in `THIRD_PARTY_LICENSES.md`.
