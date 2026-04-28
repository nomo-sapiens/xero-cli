from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ..auth.client import get_client

app = typer.Typer(help="Manage bank transactions.")
console = Console()


@app.command("list")
def list_transactions(
    days: int = typer.Option(30, "--days", "-d", help="Show transactions from the last N days"),
    account: str | None = typer.Option(
        None, "--account", "-a", help="Filter by bank account name (partial match)"
    ),
    unclassified: bool = typer.Option(
        False, "--unclassified", "-u", help="Show only transactions without an account code"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of transactions to show"),
) -> None:
    """List bank transactions."""
    from datetime import date, timedelta

    client = get_client()
    since = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "where": f"Date >= DateTime({since.replace('-', ',')})",
        "page": 1,
    }

    response = client.get("/BankTransactions", params=params)
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    transactions = response.json().get("BankTransactions", [])

    if account:
        acct_lower = account.lower()
        transactions = [
            tx
            for tx in transactions
            if acct_lower in tx.get("BankAccount", {}).get("Name", "").lower()
        ]

    if unclassified:
        transactions = [
            tx
            for tx in transactions
            if not any(li.get("AccountCode") for li in tx.get("LineItems", []))
        ]

    transactions = transactions[:limit]

    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
        return

    table = Table(title=f"Bank Transactions (last {days} days)", show_lines=False)
    table.add_column("Transaction ID", width=36, no_wrap=True)
    table.add_column("Date", width=12)
    table.add_column("Description")
    table.add_column("Bank Account")
    table.add_column("Type", width=8)
    table.add_column("Account Code", width=14)
    table.add_column("Amount", justify="right", width=12)

    for tx in transactions:
        line_items = tx.get("LineItems", [])
        acct_code = line_items[0].get("AccountCode", "—") if line_items else "—"
        desc = _get_description(tx)

        table.add_row(
            tx.get("BankTransactionID", "—"),
            tx.get("DateString", "")[:10],
            desc[:50] + ("…" if len(desc) > 50 else ""),
            tx.get("BankAccount", {}).get("Name", "—"),
            tx.get("Type", "—"),
            f"[dim]{acct_code}[/dim]" if acct_code == "—" else acct_code,
            f"{tx.get('Total', 0):,.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]{len(transactions)} transaction(s) shown[/dim]")


@app.command("set-account")
def set_account(
    transaction_id: str = typer.Argument(help="BankTransactionID (UUID)"),
    account_code: str = typer.Argument(help="Account code to assign (e.g. 420)"),
) -> None:
    """Set the account code on a bank transaction."""
    client = get_client()

    response = client.get(f"/BankTransactions/{transaction_id}")
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    transactions = response.json().get("BankTransactions", [])
    if not transactions:
        console.print(f"[red]Transaction not found:[/red] {transaction_id}")
        raise typer.Exit(1)

    tx = dict(transactions[0])
    line_items = tx.get("LineItems", [{}])
    if line_items:
        line_items[0]["AccountCode"] = account_code
    else:
        line_items = [{"AccountCode": account_code}]
    tx["LineItems"] = line_items

    resp = client.post("/BankTransactions", json={"BankTransactions": [tx]})
    if resp.status_code in (200, 201):
        desc = _get_description(tx)
        console.print(f"[green]Updated:[/green] {desc[:60]} → account code [bold]{account_code}[/bold]")
    else:
        console.print(f"[red]Error {resp.status_code}:[/red] {resp.text}")
        raise typer.Exit(1)


def _get_description(tx: dict) -> str:
    line_items = tx.get("LineItems", [])
    if line_items and line_items[0].get("Description"):
        return line_items[0]["Description"]
    return tx.get("Reference", tx.get("BankTransactionID", ""))


