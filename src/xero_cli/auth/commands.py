from __future__ import annotations

import time
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table

from ..config.settings import get_settings
from .flow import login
from .token_store import TokenStore

app = typer.Typer(help="Manage Xero authentication.")
console = Console()


@app.command()
def login_cmd(
    ctx: typer.Context,
) -> None:
    """Authenticate with Xero via OAuth2."""
    settings = get_settings()
    token_data = login(settings)
    console.print(
        f"\n[green]Successfully authenticated![/green] "
        f"Connected to [bold]{token_data['tenant_name']}[/bold]"
    )


# Register as "login" in the CLI
login_cmd.name = "login"  # type: ignore[attr-defined]


@app.command()
def status() -> None:
    """Show current authentication status."""
    store = TokenStore()
    token_data = store.load()

    if not token_data:
        console.print("[yellow]Not authenticated.[/yellow] Run [bold]xero auth login[/bold].")
        raise typer.Exit(1)

    expires_at = token_data.get("expires_at", 0)
    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    is_valid = expires_at > time.time()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Organization", token_data.get("tenant_name", "Unknown"))
    table.add_row("Tenant ID", token_data.get("tenant_id", "Unknown"))
    table.add_row(
        "Access token",
        f"[green]valid[/green] (expires {expires_dt.strftime('%Y-%m-%d %H:%M UTC')})"
        if is_valid
        else "[red]expired[/red]",
    )

    console.print("\n[bold]Authentication Status[/bold]")
    console.print(table)
    console.print()


@app.command()
def logout() -> None:
    """Remove stored credentials."""
    store = TokenStore()
    store.clear()
    console.print("[green]Logged out.[/green] Credentials removed from keychain.")
