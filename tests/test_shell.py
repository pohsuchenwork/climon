"""Tests for the interactive shell command interpreter."""

from __future__ import annotations

import pytest

from climon.cli.shell import interpret


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("quit", "quit"),
        ("exit", "quit"),
        ("Q", "quit"),
        ("", "empty"),
        ("   ", "empty"),
        ("help", "help"),
        ("?", "help"),
        ("play", "play"),
        ("PLAY", "play"),
        ("battle", "play"),
        ("online", "online"),
        ("legal", "legal"),
        ("about", "legal"),
        ("Notices", "legal"),
        ("xyzzy", "unknown:xyzzy"),
    ],
)
def test_interpret(line: str, expected: str) -> None:
    assert interpret(line) == expected
