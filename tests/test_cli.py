"""Tests for the climon command-line entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from climon import __version__
from climon.cli.main import app

runner = CliRunner()


def _accept(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treat the consent gate as already accepted, so shell tests reach the menu."""
    monkeypatch.setattr("climon.consent.has_accepted", lambda: True)


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "play" in result.stdout
    assert "online" in result.stdout


def test_bare_invocation_opens_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    _accept(monkeypatch)
    result = runner.invoke(app, [], input="quit\n")
    assert result.exit_code == 0
    assert "play" in result.stdout


def test_start_command_opens_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    _accept(monkeypatch)
    result = runner.invoke(app, ["start"], input="quit\n")
    assert result.exit_code == 0
    assert "play" in result.stdout


def test_first_run_gate_blocks_until_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A fresh user who does not type 'agree' is warned and never reaches the menu.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, [], input="quit\n")
    assert result.exit_code == 0
    assert "WARNING 1 of 3" in result.stdout
    assert "did not accept" in result.stdout
    assert "Type a command" not in result.stdout  # the menu banner never showed


def test_first_run_gate_accepts_then_opens_shell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, [], input="agree\nquit\n")
    assert result.exit_code == 0
    assert "play" in result.stdout  # the menu banner shows after accepting


def test_help_lists_start() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout


def test_legal_command_shows_affiliation() -> None:
    result = runner.invoke(app, ["legal"])
    assert result.exit_code == 0
    assert "not affiliated" in result.stdout
    assert "AS IS" in result.stdout
