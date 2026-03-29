from __future__ import annotations

import typer
from rich.console import Console

from . import __version__
from .auth import commands as auth_commands
from .invoices import commands as invoice_commands
from .reports import commands as report_commands
from .transactions import commands as transaction_commands

app = typer.Typer(
    name="xero",
    help="AI-powered Xero CLI — manage invoices, transactions, and reports from the terminal.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"xero-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


app.add_typer(auth_commands.app, name="auth")
app.add_typer(invoice_commands.app, name="invoices")
app.add_typer(transaction_commands.app, name="transactions")
app.add_typer(report_commands.app, name="reports")
