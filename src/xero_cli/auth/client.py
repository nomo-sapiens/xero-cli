from __future__ import annotations

import time
from typing import Any

import httpx
import typer
from rich.console import Console

from ..config.settings import get_settings
from .flow import refresh_token
from .token_store import TokenStore

console = Console()

XERO_API_BASE = "https://api.xero.com/api.xro/2.0"


def get_token() -> dict[str, Any]:
    """Return a valid token dict, refreshing automatically if needed."""
    store = TokenStore()
    token_data = store.load()

    if not token_data:
        console.print("[red]Not authenticated.[/red] Run [bold]xero auth login[/bold] first.")
        raise typer.Exit(1)

    # Refresh proactively if token expires within 5 minutes
    if token_data.get("expires_at", 0) - time.time() < 300:
        settings = get_settings()
        try:
            token_data = refresh_token(token_data, settings)
            store.save(token_data)
        except Exception as e:
            console.print(
                f"[red]Token refresh failed:[/red] {e}\n"
                "Run [bold]xero auth login[/bold] to re-authenticate."
            )
            raise typer.Exit(1) from e

    return token_data


def get_client() -> httpx.Client:
    """Return an authenticated httpx Client for the Xero Accounting API."""
    token = get_token()
    return httpx.Client(
        base_url=XERO_API_BASE,
        headers={
            "Authorization": f"Bearer {token['access_token']}",
            "xero-tenant-id": token["tenant_id"],
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
