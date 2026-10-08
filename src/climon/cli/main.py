"""The ``climon`` command-line interface.

``climon --help`` lists every command. With no command (or ``climon start``),
climon opens the interactive shell where you type play / online / help / quit.
"""

from typing import Annotated

import typer

from climon import __version__

app = typer.Typer(
    name="climon",
    help="A terminal Pokemon battle game. Battle the computer or another player online.",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"climon {__version__}")
        raise typer.Exit


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show the CLImon version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Run CLImon. With no command, open the interactive shell."""
    if ctx.invoked_subcommand is not None:
        return
    from climon.cli.shell import run_shell

    run_shell()


@app.command()
def start() -> None:
    """Open the interactive CLImon menu (the same as running climon with no command)."""
    from climon.cli.shell import run_shell

    run_shell()


@app.command()
def play() -> None:
    """Battle the computer: choose your lead, then fight to the last Pokemon."""
    from climon.consent import require_acceptance

    if not require_acceptance():
        raise typer.Exit
    from climon.tui.app import ClimonApp

    ClimonApp().run()


@app.command()
def online() -> None:
    """Battle another player online: connect, then a room code or quick-match."""
    from climon.consent import require_acceptance

    if not require_acceptance():
        raise typer.Exit
    from climon.tui.app import ClimonApp

    ClimonApp(online=True).run()


@app.command()
def legal() -> None:
    """Show affiliation and legal notices (full documents are in the legal/ folder)."""
    from climon.legal import NOTICE

    typer.echo(NOTICE)
