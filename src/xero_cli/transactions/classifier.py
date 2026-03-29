from __future__ import annotations

import json
from typing import Any

import anthropic
from rich.console import Console

console = Console()

SYSTEM_PROMPT = """You are an accounting assistant for Xero. Your job is to classify bank \
transactions into the most appropriate account codes from the chart of accounts.

Rules:
- Only use account codes that exist in the provided chart of accounts.
- Base your classification on the transaction description, amount, and context.
- Use confidence "high" when you are confident, "medium" when plausible but uncertain, \
"low" when you cannot determine a good match.
- Keep reasoning to one brief sentence.

Respond with ONLY a valid JSON array (no markdown, no explanation). Each element:
{"transaction_id": "...", "account_code": "...", "account_name": "...", \
"confidence": "high|medium|low", "reasoning": "..."}"""


def classify_transactions(
    transactions: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
    anthropic_api_key: str,
    model: str = "claude-sonnet-4-6",
    batch_size: int = 20,
) -> list[dict[str, Any]]:
    """
    Classify a list of bank transactions using Claude.

    Returns a list of classification results matching the input transaction order.
    """
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    # Build a compact chart of accounts for the prompt
    account_list = [
        {"code": a["Code"], "name": a["Name"], "type": a.get("Type", "")}
        for a in accounts
        if a.get("Status") == "ACTIVE" and a.get("Code")
    ]

    results: list[dict[str, Any]] = []
    batches = [transactions[i : i + batch_size] for i in range(0, len(transactions), batch_size)]

    for batch_idx, batch in enumerate(batches, 1):
        console.print(
            f"  [dim]Classifying batch {batch_idx}/{len(batches)} "
            f"({len(batch)} transactions)...[/dim]"
        )

        tx_list = [
            {
                "transaction_id": tx.get("BankTransactionID", ""),
                "date": tx.get("DateString", "")[:10],
                "description": _get_description(tx),
                "amount": tx.get("Total", 0),
                "type": tx.get("Type", ""),
            }
            for tx in batch
        ]

        user_message = (
            f"Chart of accounts:\n{json.dumps(account_list, indent=2)}\n\n"
            f"Transactions to classify:\n{json.dumps(tx_list, indent=2)}"
        )

        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            batch_results = json.loads(raw)
            results.extend(batch_results)
        except (json.JSONDecodeError, IndexError) as e:
            console.print(f"  [yellow]Warning: Failed to parse batch {batch_idx}: {e}[/yellow]")
            # Emit low-confidence unknowns for the failed batch
            for tx in batch:
                results.append(
                    {
                        "transaction_id": tx.get("BankTransactionID", ""),
                        "account_code": "",
                        "account_name": "Unknown",
                        "confidence": "low",
                        "reasoning": "Classification failed",
                    }
                )

    return results


def _get_description(tx: dict[str, Any]) -> str:
    """Extract the best human-readable description from a transaction."""
    # Try line items first
    line_items = tx.get("LineItems", [])
    if line_items:
        desc = line_items[0].get("Description", "")
        if desc:
            return desc
    # Fall back to reference
    return tx.get("Reference", tx.get("BankTransactionID", ""))[:120]
