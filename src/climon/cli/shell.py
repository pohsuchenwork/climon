"""The interactive climon shell.

Running ``climon`` with no command drops you here, so you type ``play`` / ``help`` /
``quit`` without the ``climon`` prefix (like a git or psql prompt).
"""

from __future__ import annotations

from climon.art import LOGO, TAGLINE
from climon.legal import AFFILIATION, NOTICE

BANNER = (
    f"\n{LOGO}\n{TAGLINE}\n\n{AFFILIATION}\nType a command: play, online, legal, help, or quit."
)

HELP = (
    "Commands:\n"
    "  play     battle the computer\n"
    "  online   battle another player online\n"
    "  legal    affiliation and legal notices\n"
    "  help     show this help\n"
    "  quit     leave climon"
)


def interpret(line: str) -> str:
    """Classify a shell line as quit, empty, help, play, online, legal, or 'unknown:<line>'."""
    low = line.strip().lower()
    if low in ("quit", "exit", "q"):
        return "quit"
    if not low:
        return "empty"
    if low in ("help", "?", "h"):
        return "help"
    if low in ("play", "p", "battle"):
        return "play"
    if low == "online":
        return "online"
    if low in ("legal", "about", "notice", "notices"):
        return "legal"
    return f"unknown:{low}"


def run_shell() -> None:
    """Run the interactive shell loop until the user quits."""
    from climon.consent import require_acceptance

    if not require_acceptance():
        return
    print(BANNER)
    while True:
        try:
            line = input("climon> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        command = interpret(line)
        if command == "quit":
            break
        if command == "empty":
            continue
        if command == "help":
            print(HELP)
        elif command == "legal":
            print(NOTICE)
        elif command == "play":
            _launch_game()
        elif command == "online":
            _launch_online()
        else:
            print(f"Unknown command: {line.strip()!r}. Type 'help'.")
    print("Bye!")


def _launch_game() -> None:
    from climon.tui.app import ClimonApp

    ClimonApp().run()


def _launch_online() -> None:
    from climon.tui.app import ClimonApp

    ClimonApp(online=True).run()
