"""Short in-product legal notices.

The full documents (Terms of Service, EULA, Privacy Policy, Disclaimer) live in the
project's ``legal/`` folder; the original software license is the MIT ``LICENSE`` file.
These short notices are surfaced in the shell, the CLI, and online play so users see the
key disclaimers without leaving the terminal.
"""

from __future__ import annotations

AFFILIATION = (
    "CLImon is an unofficial, non-commercial fan project. It is not affiliated with, "
    "endorsed by, or sponsored by Nintendo, Creatures, GAME FREAK, or The Pokemon Company. "
    "Pokemon, character names, and sprite artwork are trademarks and copyrighted works of "
    "their owners; all rights in them are reserved to those owners."
)

# Attribution and the rights-holder takedown path, surfaced in the `legal` notice.
ATTRIBUTION = (
    "CLImon is free and not for sale, and claims no ownership of or rights in any "
    "third-party property. If you represent a rights holder and want CLImon, or any "
    "specific asset, removed, please open an issue on the project's GitHub repository and "
    "it will be taken down promptly."
)

# Shown when a user asks for legal info (the `legal` command / `climon legal`).
NOTICE = (
    f"{AFFILIATION}\n\n"
    f"{ATTRIBUTION}\n\n"
    "CLImon is provided AS IS, without warranty of any kind, and any online service may "
    "change, be limited, or stop at any time without liability. Use of CLImon, and "
    "especially online play, is subject to the Terms of Service, EULA, and Privacy Policy "
    "in the project's legal/ folder, and to the MIT LICENSE for the software.\n"
    "Your statutory consumer rights, where they apply, are not affected.\n\n"
    "Full documents: see the legal/ folder in the CLImon project."
)

# One short line for the online lobby (notice that online play is subject to the Terms).
ONLINE_NOTICE = "By playing online you accept the Terms of Service (see legal/)."
