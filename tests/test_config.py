"""Tests for typed configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from climon.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("CLIMON_SERVER", raising=False)
    settings = Settings()
    assert settings.server_url == "ws://localhost:8765"
    assert settings.theme == "dark"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIMON_SERVER", "wss://example.fly.dev")
    settings = Settings()
    assert settings.server_url == "wss://example.fly.dev"


def test_rejects_bad_server_url() -> None:
    with pytest.raises(ValidationError):
        Settings(server_url="http://nope")
