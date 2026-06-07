"""Typed application configuration for climon.

Settings load with this precedence: explicit constructor arguments, then
environment variables (prefixed ``CLIMON_``, with ``CLIMON_SERVER`` as a special
alias for the server URL), then a TOML file in the XDG config dir, then the
defaults below. Nothing is stored in the repository.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

APP_NAME = "climon"


def xdg_config_dir() -> Path:
    """Return the XDG config directory for climon."""
    raw = os.environ.get("XDG_CONFIG_HOME")
    base = Path(raw).expanduser() if raw else Path.home() / ".config"
    return base / APP_NAME


def config_file() -> Path:
    """Return the path to the climon config TOML file."""
    return xdg_config_dir() / "config.toml"


def acceptance_marker() -> Path:
    """Return the path of the file recording that the user accepted the no-warranty terms."""
    return xdg_config_dir() / "accepted"


class Settings(BaseSettings):
    """User-facing settings, validated at load time."""

    model_config = SettingsConfigDict(env_prefix="CLIMON_", extra="ignore")

    server_url: str = Field(
        default="ws://localhost:8765",
        validation_alias=AliasChoices("server_url", "CLIMON_SERVER"),
        description="WebSocket URL of the climon online server.",
    )
    player_name: str = Field(default="Player", min_length=1, max_length=24)
    theme: Literal["dark", "light"] = "dark"
    reduce_motion: bool = False

    @field_validator("server_url")
    @classmethod
    def _validate_server_url(cls, value: str) -> str:
        if not value.startswith(("ws://", "wss://")):
            msg = "server_url must start with ws:// or wss://"
            raise ValueError(msg)
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Precedence: explicit init args, then environment, then the TOML file.
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=config_file()),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once."""
    return Settings()
