from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..auth.client import get_client

app = typer.Typer(help="Manage invoices.")
console = Console()

STATUS_COLORS = {
    "DRAFT": "yellow",
    "SUBMITTED": "blue",
    "AUTHORISED": "green",
    "PAID": "cyan",
    "VOIDED": "dim",
    "DELETED": "red",
}


@app.command("list")
def list_invoices(
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status: DRAFT, AUTHORISED, PAID, VOIDED"
    ),
    contact: Optional[str] = typer.Option(
        None, "--contact", "-c", help="Filter by contact name (partial match)"
    ),
    days: int = typer.Option(90, "--days", "-d", help="Show invoices from the last N days"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of invoices to show"),
) -> None:
    """List invoices with optional filters."""
    from datetime import date, timedelta

    client = get_client()
    params: dict = {"page": 1}

    if status:
        params["Statuses"] = status.upper()

    since = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    params["where"] = f'Date >= DateTime({since.replace("-", ",")})'

    response = client.get("/Invoices", params=params)
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    invoices = response.json().get("Invoices", [])

    if contact:
        contact_lower = contact.lower()
        invoices = [
            inv
            for inv in invoices
            if contact_lower in inv.get("Contact", {}).get("Name", "").lower()
        ]

    invoices = invoices[:limit]

    if not invoices:
        console.print("[yellow]No invoices found.[/yellow]")
        return

    table = Table(title=f"Invoices (last {days} days)", show_lines=False)
    table.add_column("Invoice #", style="bold")
    table.add_column("Date")
    table.add_column("Due Date")
    table.add_column("Contact")
    table.add_column("Status")
    table.add_column("Amount Due", justify="right")
    table.add_column("Total", justify="right")

    for inv in invoices:
        inv_status = inv.get("Status", "")
        color = STATUS_COLORS.get(inv_status, "white")
        table.add_row(
            inv.get("InvoiceNumber", inv.get("InvoiceID", "")[:8]),
            _fmt_date(inv.get("DateString", "")),
            _fmt_date(inv.get("DueDateString", "")),
            inv.get("Contact", {}).get("Name", "—"),
            f"[{color}]{inv_status}[/{color}]",
            f"{inv.get('CurrencyCode', '')} {inv.get('AmountDue', 0):,.2f}",
            f"{inv.get('CurrencyCode', '')} {inv.get('Total', 0):,.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]{len(invoices)} invoice(s) shown[/dim]")


@app.command("get")
def get_invoice(invoice_id: str = typer.Argument(..., help="Invoice ID or invoice number")) -> None:
    """Show details for a single invoice."""
    client = get_client()
    response = client.get(f"/Invoices/{invoice_id}")
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    invoices = response.json().get("Invoices", [])
    if not invoices:
        console.print(f"[red]Invoice '{invoice_id}' not found.[/red]")
        raise typer.Exit(1)

    inv = invoices[0]
    inv_status = inv.get("Status", "")
    color = STATUS_COLORS.get(inv_status, "white")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Invoice #", inv.get("InvoiceNumber", "—"))
    table.add_row("Type", inv.get("Type", "—"))
    table.add_row("Status", f"[{color}]{inv_status}[/{color}]")
    table.add_row("Contact", inv.get("Contact", {}).get("Name", "—"))
    table.add_row("Date", _fmt_date(inv.get("DateString", "")))
    table.add_row("Due Date", _fmt_date(inv.get("DueDateString", "")))
    table.add_row("Sub Total", f"{inv.get('CurrencyCode', '')} {inv.get('SubTotal', 0):,.2f}")
    table.add_row("Tax", f"{inv.get('CurrencyCode', '')} {inv.get('TotalTax', 0):,.2f}")
    table.add_row("Total", f"[bold]{inv.get('CurrencyCode', '')} {inv.get('Total', 0):,.2f}[/bold]")
    table.add_row("Amount Due", f"{inv.get('CurrencyCode', '')} {inv.get('AmountDue', 0):,.2f}")

    console.print(f"\n[bold]Invoice Details[/bold]")
    console.print(table)

    line_items = inv.get("LineItems", [])
    if line_items:
        console.print("\n[bold]Line Items[/bold]")
        li_table = Table(show_lines=True)
        li_table.add_column("Description")
        li_table.add_column("Qty", justify="right")
        li_table.add_column("Unit Price", justify="right")
        li_table.add_column("Account")
        li_table.add_column("Amount", justify="right")
        for item in line_items:
            li_table.add_row(
                item.get("Description", "—"),
                str(item.get("Quantity", "")),
                f"{item.get('UnitAmount', 0):,.2f}",
                item.get("AccountCode", "—"),
                f"{item.get('LineAmount', 0):,.2f}",
            )
        console.print(li_table)
    console.print()


def _fmt_date(date_str: str) -> str:
    """Format Xero date strings like '2024-03-15T00:00:00' to '2024-03-15'."""
    if not date_str:
        return "—"
    return date_str[:10]
