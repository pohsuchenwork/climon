"""Configure logging to a file under the XDG state dir, never to stdout.

The TUI owns the terminal, so log records must not reach stdout or stderr. During
development the Textual console streams these records instead.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_NAME = "climon"
_HANDLER_NAME = "climon-file"


def xdg_state_dir() -> Path:
    """Return the XDG state directory for climon."""
    raw = os.environ.get("XDG_STATE_HOME")
    base = Path(raw).expanduser() if raw else Path.home() / ".local" / "state"
    return base / APP_NAME


def log_file() -> Path:
    """Return the path to the climon log file."""
    return xdg_state_dir() / "climon.log"


def setup_logging(level: int = logging.INFO) -> Path:
    """Send the root logger to a rotating file under the XDG state dir.

    Returns the log file path. Calling this more than once is safe; the file
    handler is installed only once.
    """
    path = log_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(level)
    if not any(handler.get_name() == _HANDLER_NAME for handler in root.handlers):
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.set_name(_HANDLER_NAME)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
        root.addHandler(handler)
    return path
