from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..auth.client import get_client

app = typer.Typer(help="Generate financial reports.")
console = Console()


@app.command("profit-loss")
def profit_loss(
    months: int = typer.Option(12, "--months", "-m", help="Number of months to report on"),
    from_date: Optional[str] = typer.Option(
        None, "--from", help="Start date (YYYY-MM-DD). Overrides --months."
    ),
    to_date: Optional[str] = typer.Option(
        None, "--to", help="End date (YYYY-MM-DD). Defaults to today."
    ),
) -> None:
    """Show Profit & Loss report."""
    today = date.today()
    end = today.strftime("%Y-%m-%d") if not to_date else to_date
    start = (today - timedelta(days=months * 30)).strftime("%Y-%m-%d") if not from_date else from_date

    client = get_client()
    response = client.get(
        "/Reports/ProfitAndLoss",
        params={"fromDate": start, "toDate": end},
    )
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    reports = response.json().get("Reports", [])
    if not reports:
        console.print("[yellow]No report data available.[/yellow]")
        return

    report = reports[0]
    console.print(f"\n[bold]{report.get('ReportName', 'Profit & Loss')}[/bold]")
    console.print(f"[dim]{report.get('ReportDate', '')}[/dim]\n")

    _render_report_rows(report.get("Rows", []))
    console.print()


@app.command("balance-sheet")
def balance_sheet(
    as_of: Optional[str] = typer.Option(
        None, "--date", help="Balance sheet date (YYYY-MM-DD). Defaults to today."
    ),
) -> None:
    """Show Balance Sheet report."""
    report_date = as_of or date.today().strftime("%Y-%m-%d")

    client = get_client()
    response = client.get(
        "/Reports/BalanceSheet",
        params={"date": report_date},
    )
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    reports = response.json().get("Reports", [])
    if not reports:
        console.print("[yellow]No report data available.[/yellow]")
        return

    report = reports[0]
    console.print(f"\n[bold]{report.get('ReportName', 'Balance Sheet')}[/bold]")
    console.print(f"[dim]{report.get('ReportDate', '')}[/dim]\n")

    _render_report_rows(report.get("Rows", []))
    console.print()


@app.command("aged-receivables")
def aged_receivables(
    as_of: Optional[str] = typer.Option(
        None, "--date", help="Report date (YYYY-MM-DD). Defaults to today."
    ),
) -> None:
    """Show Aged Receivables report (outstanding invoices by contact)."""
    report_date = as_of or date.today().strftime("%Y-%m-%d")

    client = get_client()
    response = client.get(
        "/Reports/AgedReceivablesByContact",
        params={"date": report_date},
    )
    if response.status_code != 200:
        console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
        raise typer.Exit(1)

    reports = response.json().get("Reports", [])
    if not reports:
        console.print("[yellow]No report data available.[/yellow]")
        return

    report = reports[0]
    console.print(f"\n[bold]{report.get('ReportName', 'Aged Receivables')}[/bold]")
    console.print(f"[dim]{report.get('ReportDate', '')}[/dim]\n")

    _render_report_rows(report.get("Rows", []))
    console.print()


def _render_report_rows(rows: list[dict], indent: int = 0) -> None:
    """Recursively render Xero report rows as rich tables."""
    # Collect Section and Row items into a table
    for row in rows:
        row_type = row.get("RowType", "")

        if row_type == "Header":
            cells = row.get("Cells", [])
            headers = [c.get("Value", "") for c in cells]
            table = Table(show_header=True, box=None, padding=(0, 2))
            for h in headers:
                justify = "right" if headers.index(h) > 0 else "left"
                table.add_column(h, justify=justify, style="bold dim")
            console.print(table)

        elif row_type == "Section":
            title = row.get("Title", "")
            if title:
                console.print(f"\n[bold]{' ' * indent}{title}[/bold]")
            _render_report_rows(row.get("Rows", []), indent=indent + 2)

        elif row_type in ("Row", "SummaryRow"):
            cells = row.get("Cells", [])
            values = [c.get("Value", "") for c in cells]
            if not values:
                continue
            label = values[0]
            nums = values[1:]
            is_summary = row_type == "SummaryRow"
            style = "bold" if is_summary else ""
            # Print as indented line
            label_fmt = f"[{style}]{' ' * indent}{label}[/{style}]" if style else f"{' ' * indent}{label}"
            nums_fmt = "  ".join(
                f"[{style}]{n:>14}[/{style}]" if style else f"{n:>14}" for n in nums
            )
            console.print(f"{label_fmt:<50} {nums_fmt}")
