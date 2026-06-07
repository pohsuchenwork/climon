# Changelog

All notable changes to climon are documented here. The format follows Keep a
Changelog, and the project aims to follow semantic versioning.

## [Unreleased]

### Added
- Project bootstrap: uv plus hatchling packaging; the Textual, Typer, websockets,
  and pydantic stack; Ruff, mypy (strict), and pytest tooling; and GitHub Actions CI.
- Runnable `climon` entry point with `--version`, `--help`, and placeholder
  `play` and `online` commands.
- Typed configuration (pydantic-settings, XDG TOML) and file logging (XDG state).
- Pure 3v3 battle engine: data model, the starter type triangle, the three
  starters with movesets, a seeded damage formula, and the turn resolver
  (ordering, status moves, faint, forced replacement, team-wipe win), with
  deterministic tests.
- Sprite pipeline (chafa to cached .ans art) and the static battle TUI: the
  classic full-screen layout with both info boxes, HP bars, party balls, and the
  FIGHT / BAG / POKEMON / RUN command grid, fitting an 80x24 terminal. `climon
  play` opens a preview.
