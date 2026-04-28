from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ..auth.client import get_client

app = typer.Typer(help="Manage chart of accounts.")
console = Console()


@app.command("list")
def list_accounts(
    type_filter: str | None = typer.Option(
        None, "--type", "-t", help="Filter by account type (e.g. EXPENSE, REVENUE, ASSET)"
    ),
    status: str | None = typer.Option(
        None, "--status", "-s", help="Filter by status: ACTIVE, ARCHIVED"
    ),
) -> None:
    """List chart of accounts."""
    client = get_client()
    response = client.get("/Accounts")
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    accounts = response.json().get("Accounts", [])

    if type_filter:
        accounts = [a for a in accounts if a.get("Type", "").upper() == type_filter.upper()]

    if status:
        accounts = [a for a in accounts if a.get("Status", "").upper() == status.upper()]

    if not accounts:
        console.print("[yellow]No accounts found.[/yellow]")
        return

    table = Table(title="Chart of Accounts", show_lines=False)
    table.add_column("Code", width=8)
    table.add_column("Name")
    table.add_column("Type", width=16)
    table.add_column("Tax Type", width=16)
    table.add_column("Status", width=10)

    for acct in sorted(accounts, key=lambda a: a.get("Code") or ""):
        status_val = acct.get("Status", "—")
        status_display = f"[dim]{status_val}[/dim]" if status_val == "ARCHIVED" else status_val
        table.add_row(
            acct.get("Code") or "—",
            acct.get("Name", "—"),
            acct.get("Type", "—"),
            acct.get("TaxType") or "—",
            status_display,
        )

    console.print(table)
    console.print(f"\n[dim]{len(accounts)} account(s) shown[/dim]")


@app.command("add")
def add_account(
    name: str = typer.Option(..., "--name", "-n", help="Account name"),
    type_: str = typer.Option(..., "--type", "-t", help="Account type (e.g. EXPENSE, REVENUE, ASSET, LIABILITY, EQUITY, BANK)"),
    code: str | None = typer.Option(None, "--code", "-c", help="Account code (e.g. 420)"),
    tax_type: str | None = typer.Option(None, "--tax-type", help="Tax type (e.g. INPUT, OUTPUT, NONE)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Account description"),
) -> None:
    """Add a new account to the chart of accounts."""
    client = get_client()

    payload: dict = {"Name": name, "Type": type_.upper()}
    if code:
        payload["Code"] = code
    if tax_type:
        payload["TaxType"] = tax_type.upper()
    if description:
        payload["Description"] = description

    response = client.put("/Accounts", json={"Accounts": [payload]})
    if response.status_code not in (200, 201):
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    created = response.json().get("Accounts", [{}])[0]
    console.print(
        f"[green]Created:[/green] {created.get('Code') or '—'}  {created.get('Name')}  "
        f"({created.get('Type')})"
    )
