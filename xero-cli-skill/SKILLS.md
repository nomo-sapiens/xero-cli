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
ANTHROPIC_API_KEY=...    # For transaction classification only
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

## Workflow 2: Automated Transaction Classification

Classify unclassified bank transactions using Claude. Fully non-interactive with `--batch`.

```bash
# Step 1: See what's unclassified (read-only, no changes)
xero transactions list --unclassified --days 30

# Step 2: Preview AI classifications without applying them
xero transactions classify --dry-run --days 30

# Step 3: Auto-apply all high-confidence classifications
xero transactions classify --batch --days 30

# Classify a longer window
xero transactions classify --batch --days 90

# Use a specific Claude model
xero transactions classify --batch --model claude-opus-4-6 --days 30
```

**Confidence behaviour in `--batch` mode**:
- `high` → applied automatically
- `medium` / `low` → skipped (not applied)

For complete automation including medium/low confidence items, use `--dry-run` first to review, then run `--batch` for the high-confidence subset.

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

# 3. Preview AI classifications (dry run)
xero transactions classify --dry-run --days 30

# 4. Apply high-confidence classifications
xero transactions classify --batch --days 30

# 5. Review remaining unclassified (medium/low confidence were skipped)
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
# Classify all transactions for the month
xero transactions classify --batch --days 31

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
- `ANTHROPIC_API_KEY` not set → required for `xero transactions classify`
- API errors → check Xero connectivity and token validity via `xero auth status`
