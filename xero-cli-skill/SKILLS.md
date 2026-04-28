# xero-cli Agent Skills

A workflow guide for AI agents using the xero-cli to manage Xero accounting.

For complete option details, see [REFERENCE.md](./REFERENCE.md).

---

## Prerequisites

### One-time human setup

Authentication requires a browser OAuth2 flow — this must be done once by a human:

```bash
# Single org:
xero auth login

# Multiple orgs — auto-select by name to avoid the interactive prompt:
xero auth login --tenant "Acme Ltd"
```

After login, tokens are stored in the OS keychain and **auto-refresh** before expiry. Agents can run all subsequent commands without re-authenticating.

### Required environment variables

```bash
XERO_CLIENT_ID=...       # From Xero developer portal
XERO_CLIENT_SECRET=...   # From Xero developer portal
```

### Verify auth before running workflows

```bash
xero auth status
```

Exits `0` if authenticated, `1` if not. Use as a pre-flight check.

---

## Workflow 1: Invoice Review

Find unpaid invoices and inspect outstanding ones.

```bash
# List all AUTHORISED (unpaid) invoices from the last 90 days
xero invoices list --status AUTHORISED --days 90

# Filter to a specific client
xero invoices list --status AUTHORISED --contact "Acme"

# Inspect a specific invoice in detail
xero invoices get INV-0042

# Find all overdue invoices (AUTHORISED = sent but not paid)
xero invoices list --status AUTHORISED --days 180 --limit 100
```

---

## Workflow 2: Agent-Driven Transaction Classification

> **Important**: Always confirm with the user before applying any classifications to Xero. Present your proposed classifications and wait for explicit approval before running any `set-account` commands.

Classification is performed by the agent (you) using CLI commands only. Use the steps below.

### Step 1 — Fetch data

```bash
# Get unclassified transactions (Transaction IDs are shown in output)
xero transactions list --unclassified --days 30

# Get the chart of accounts (to know valid account codes)
xero accounts list

# If a suitable account doesn't exist, create it first — confirm with the user before doing so
xero accounts add --name "Office Expenses" --type EXPENSE --code 420
xero accounts add --name "Software & Subscriptions" --type EXPENSE --code 460
```

### Step 2 — Classify

For each unclassified transaction, reason about the most appropriate account code based on:
- The transaction description / reference
- The transaction type (SPEND / RECEIVE)
- The amount and counterparty
- The chart of accounts

Assign a **confidence level** to each classification:

| Confidence | Colour | Meaning |
|---|---|---|
| `high` | green | Strong match — description clearly maps to one account |
| `medium` | yellow | Probable match — some ambiguity |
| `low` | red | Uncertain — insufficient context to classify reliably |

### Step 3 — Present results and confirm

Display a proposed classification table with columns: `#`, `Transaction ID`, `Date`, `Description`, `Amount`, `Suggested Account`, `Confidence`, `Reasoning`.

**Always ask the user to confirm before applying anything.** For example:

> "I've classified 8 transactions above. Shall I apply the 5 high-confidence ones now? The 3 medium-confidence ones are listed — confirm each or skip."

Do not proceed to Step 4 until the user has approved.

### Step 4 — Apply approved classifications

Use `xero transactions set-account` for each approved transaction:

```bash
xero transactions set-account <transaction_id> <account_code>
```

After applying, report a summary: `N applied, N skipped, N error(s)`.

---

## Workflow 3: Financial Reporting

All report commands are fully non-interactive.

```bash
# Profit & Loss for the current financial year (last 12 months)
xero reports profit-loss

# P&L for a custom date range
xero reports profit-loss --from 2025-07-01 --to 2026-06-30

# P&L for last 3 months
xero reports profit-loss --months 3

# Balance sheet as of today
xero reports balance-sheet

# Balance sheet at end of last financial year
xero reports balance-sheet --date 2025-06-30

# Aged receivables (who owes money)
xero reports aged-receivables

# Aged receivables at a past date
xero reports aged-receivables --date 2026-01-01
```

---

## Workflow 4: Accounts Receivable Monitoring

Identify overdue invoices and clients with outstanding balances.

```bash
# Show aged receivables summary
xero reports aged-receivables

# Find all outstanding invoices older than 60 days
xero invoices list --status AUTHORISED --days 180 --limit 200

# Check a specific client's unpaid invoices
xero invoices list --status AUTHORISED --contact "Acme Corp" --days 365
```

---

## Workflow 5: Full Bookkeeping Pipeline

End-to-end pipeline combining transaction classification and financial reporting.

```bash
# 1. Verify authentication
xero auth status

# 2. Check what transactions need classification
xero transactions list --unclassified --days 30

# 3. Fetch chart of accounts
xero accounts list

# 4. Classify (agent-driven — see Workflow 2)
#    Reason about each transaction, present confidence-coloured table,
#    confirm with user, then apply approved classifications:
xero transactions set-account <transaction_id> <account_code>

# 5. Review remaining unclassified
xero transactions list --unclassified --days 30

# 6. Pull updated P&L to confirm numbers
xero reports profit-loss --months 1

# 7. Check balance sheet
xero reports balance-sheet

# 8. Review outstanding receivables
xero reports aged-receivables
```

---

## Workflow 6: Month-End Close

```bash
# Classify all transactions for the month (agent-driven — see Workflow 2)
xero transactions list --unclassified --days 31
xero accounts list
# Reason about each transaction, present table, confirm with user, then:
xero transactions set-account <transaction_id> <account_code>

# Review invoices sent this month
xero invoices list --status AUTHORISED --days 31

# Generate month-end reports
xero reports profit-loss --from 2026-03-01 --to 2026-03-31
xero reports balance-sheet --date 2026-03-31
xero reports aged-receivables --date 2026-03-31
```

---

## Error Handling

All commands exit `0` on success and `1` on failure. Errors are printed to stdout with `[red]Error:[/red]` prefix.

Common failure causes:
- Not authenticated → run `xero auth login`
- API errors → check Xero connectivity and token validity via `xero auth status`
