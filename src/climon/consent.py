"""First-run consent gate: the user must accept the no-warranty, no-liability terms.

Shown the first time CLImon is launched (and again if the terms version changes). The
acceptance is recorded in the config dir so it is asked once, not on every launch. Kept
out of the engine and UI so the CLI entry points and tests can call it directly. The
``read``/``write`` hooks make it testable without touching the real terminal.
"""

from __future__ import annotations

from collections.abc import Callable

from climon.config import acceptance_marker
from climon.legal import AFFILIATION

# Bump when the terms change so existing users are asked to accept again.
ACCEPTANCE_VERSION = "1"

WARNING = f"""\
==================  PLEASE READ BEFORE USING  ==================
CLImon is a free, unofficial fan project, provided AS IS.

  WARNING 1 of 3 - NO WARRANTY
  CLImon comes with absolutely no warranty of any kind. It may
  not work, may stop working, or may behave unexpectedly.

  WARNING 2 of 3 - USE AT YOUR OWN RISK
  You install and run CLImon entirely at your own risk. You are
  responsible for your own computer, your data, and anything
  that happens on your machine.

  WARNING 3 of 3 - NO LIABILITY
  To the maximum extent permitted by law, the author is not
  liable for any damage, data loss, or harm of any kind arising
  from installing or using CLImon. If something breaks, that is
  not the author's responsibility.

{AFFILIATION}

Full notices: run 'climon legal' or see the legal/ folder.
================================================================"""

PROMPT = "Type 'agree' to accept and use CLImon, or anything else to exit: "


def has_accepted() -> bool:
    """True if this user has already accepted the current terms version."""
    try:
        return acceptance_marker().read_text(encoding="utf-8").strip() == ACCEPTANCE_VERSION
    except OSError:
        return False


def record_acceptance() -> None:
    """Persist that the user accepted the current terms (best effort)."""
    marker = acceptance_marker()
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(ACCEPTANCE_VERSION, encoding="utf-8")
    except OSError:
        pass  # if we cannot persist, we simply ask again next time


def require_acceptance(
    *,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> bool:
    """Ensure the terms are accepted. Returns True to proceed, False to abort launch."""
    if has_accepted():
        return True
    write(WARNING)
    try:
        answer = read(PROMPT)
    except (EOFError, KeyboardInterrupt):
        write("\nNo response received, so CLImon will not run.")
        return False
    if answer.strip().lower() != "agree":
        write("You did not accept the terms, so CLImon will not run.")
        return False
    record_acceptance()
    write("Thanks. Enjoy CLImon.  (Review the notices any time with 'climon legal'.)\n")
    return True
