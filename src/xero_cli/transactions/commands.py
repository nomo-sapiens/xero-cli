from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..auth.client import get_client, get_token
from ..config.settings import get_settings

app = typer.Typer(help="Manage bank transactions.")
console = Console()

CONFIDENCE_COLORS = {"high": "green", "medium": "yellow", "low": "red"}


@app.command("list")
def list_transactions(
    days: int = typer.Option(30, "--days", "-d", help="Show transactions from the last N days"),
    account: Optional[str] = typer.Option(
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
        "where": f'Date >= DateTime({since.replace("-", ",")})',
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
            if not any(
                li.get("AccountCode") for li in tx.get("LineItems", [])
            )
        ]

    transactions = transactions[:limit]

    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
        return

    table = Table(title=f"Bank Transactions (last {days} days)", show_lines=False)
    table.add_column("Date")
    table.add_column("Description")
    table.add_column("Bank Account")
    table.add_column("Type")
    table.add_column("Account Code")
    table.add_column("Amount", justify="right")

    for tx in transactions:
        line_items = tx.get("LineItems", [])
        acct_code = line_items[0].get("AccountCode", "—") if line_items else "—"
        desc = _get_description(tx)

        table.add_row(
            tx.get("DateString", "")[:10],
            desc[:50] + ("…" if len(desc) > 50 else ""),
            tx.get("BankAccount", {}).get("Name", "—"),
            tx.get("Type", "—"),
            f"[dim]{acct_code}[/dim]" if acct_code == "—" else acct_code,
            f"{tx.get('Total', 0):,.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]{len(transactions)} transaction(s) shown[/dim]")


@app.command("classify")
def classify(
    days: int = typer.Option(30, "--days", "-d", help="Classify transactions from the last N days"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show classifications without applying them to Xero"
    ),
    batch: bool = typer.Option(
        False,
        "--batch",
        help="Apply all high-confidence classifications without confirmation",
    ),
    model: str = typer.Option("claude-sonnet-4-6", "--model", "-m", help="Claude model to use"),
) -> None:
    """AI-powered bank transaction classification using Claude."""
    from datetime import date, timedelta

    from .classifier import classify_transactions

    settings = get_settings()
    if not settings.anthropic_api_key:
        console.print(
            "[red]Error:[/red] ANTHROPIC_API_KEY is not set.\n"
            "Add it to your [bold].env[/bold] file or set the environment variable."
        )
        raise typer.Exit(1)

    client = get_client()
    token = get_token()

    # Fetch unclassified transactions
    since = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    console.print(f"\nFetching unclassified transactions from the last {days} days...")

    tx_response = client.get(
        "/BankTransactions",
        params={
            "where": f'Date >= DateTime({since.replace("-", ",")})',
            "page": 1,
        },
    )
    if tx_response.status_code != 200:
        console.print(f"[red]Error {tx_response.status_code}:[/red] {tx_response.text}")
        raise typer.Exit(1)

    all_transactions = tx_response.json().get("BankTransactions", [])
    # Only classify transactions with no account code on their line items
    unclassified = [
        tx
        for tx in all_transactions
        if tx.get("Status") == "AUTHORISED"
        and not any(li.get("AccountCode") for li in tx.get("LineItems", []))
    ]

    if not unclassified:
        console.print("[green]All transactions are already classified.[/green]")
        return

    console.print(f"Found [bold]{len(unclassified)}[/bold] unclassified transaction(s).")

    # Fetch chart of accounts
    acct_response = client.get("/Accounts")
    if acct_response.status_code != 200:
        console.print(f"[red]Error fetching accounts:[/red] {acct_response.text}")
        raise typer.Exit(1)
    accounts = acct_response.json().get("Accounts", [])

    console.print(f"Loaded [bold]{len(accounts)}[/bold] accounts from chart of accounts.")
    console.print("\nCalling Claude for classification...\n")

    classifications = classify_transactions(
        unclassified,
        accounts,
        anthropic_api_key=settings.anthropic_api_key,
        model=model,
    )

    # Build a lookup map: transaction_id -> classification
    classification_map = {c["transaction_id"]: c for c in classifications}

    # Display results table
    table = Table(
        title="Classification Results",
        show_lines=True,
        title_style="bold",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Date", width=12)
    table.add_column("Description", max_width=40)
    table.add_column("Amount", justify="right", width=12)
    table.add_column("Suggested Account", width=28)
    table.add_column("Conf", width=6)
    table.add_column("Reasoning", max_width=40)

    for i, tx in enumerate(unclassified, 1):
        tx_id = tx.get("BankTransactionID", "")
        cls = classification_map.get(tx_id, {})
        conf = cls.get("confidence", "low")
        color = CONFIDENCE_COLORS.get(conf, "white")
        acct_display = (
            f"{cls['account_code']} - {cls['account_name']}"
            if cls.get("account_code")
            else "[dim]—[/dim]"
        )
        desc = _get_description(tx)
        table.add_row(
            str(i),
            tx.get("DateString", "")[:10],
            desc[:40] + ("…" if len(desc) > 40 else ""),
            f"{tx.get('Total', 0):,.2f}",
            acct_display,
            f"[{color}]{conf}[/{color}]",
            cls.get("reasoning", "—"),
        )

    console.print(table)
    console.print()

    if dry_run:
        console.print("[yellow]Dry run — no changes applied to Xero.[/yellow]")
        return

    # Determine which transactions to apply
    to_apply = [
        tx
        for tx in unclassified
        if classification_map.get(tx.get("BankTransactionID", ""), {}).get("account_code")
        and (
            batch
            or classification_map[tx["BankTransactionID"]]["confidence"] == "high"
            or _confirm_single(tx, classification_map[tx["BankTransactionID"]])
        )
    ]

    if not to_apply:
        console.print("[yellow]No classifications applied.[/yellow]")
        return

    console.print(f"\nApplying [bold]{len(to_apply)}[/bold] classification(s) to Xero...")
    applied = 0
    errors = 0

    for tx in to_apply:
        tx_id = tx["BankTransactionID"]
        cls = classification_map[tx_id]
        # Build update payload — Xero requires the full transaction in PUT
        updated_tx = dict(tx)
        line_items = updated_tx.get("LineItems", [{}])
        if line_items:
            line_items[0]["AccountCode"] = cls["account_code"]
        else:
            line_items = [{"AccountCode": cls["account_code"]}]
        updated_tx["LineItems"] = line_items

        resp = client.post(
            "/BankTransactions",
            json={"BankTransactions": [updated_tx]},
        )
        if resp.status_code in (200, 201):
            applied += 1
        else:
            errors += 1
            console.print(f"  [red]Failed to update {tx_id}:[/red] {resp.text[:120]}")

    console.print(
        f"\n[green]Done.[/green] {applied} classified"
        + (f", {errors} error(s)" if errors else "")
        + "."
    )


def _get_description(tx: dict) -> str:
    line_items = tx.get("LineItems", [])
    if line_items and line_items[0].get("Description"):
        return line_items[0]["Description"]
    return tx.get("Reference", tx.get("BankTransactionID", ""))


def _confirm_single(tx: dict, cls: dict) -> bool:
    desc = _get_description(tx)[:50]
    acct = f"{cls.get('account_code')} - {cls.get('account_name')}"
    prompt = f"  Apply '{acct}' to '{desc}'? [y/N]"
    return typer.confirm(prompt, default=False)
