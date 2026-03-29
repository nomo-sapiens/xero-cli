# xero-cli Reference

Complete reference for every command, option, output, and configuration value.

---

## Installation

```bash
pip install xero-cli
# or from source:
pip install -e .
```

Entry point: `xero`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `XERO_CLIENT_ID` | Yes (for login) | OAuth2 client ID from Xero developer portal |
| `XERO_CLIENT_SECRET` | Yes (for login) | OAuth2 client secret from Xero developer portal |
| `ANTHROPIC_API_KEY` | Yes (for classify) | Anthropic API key for Claude-powered classification |

Can be set via:
- Environment variables
- `.env` file (loaded automatically via python-dotenv)
- `~/.config/xero-cli/config.toml`

---

## Global Options

| Flag | Description |
|---|---|
| `--version`, `-v` | Show version and exit |
| `--help` | Show help for any command |

---

## `xero auth` — Authentication

### `xero auth login`

Authenticate with Xero via OAuth2. Opens a browser window for authorization.

**Interactive**: Yes — opens browser. If multiple Xero organizations exist, prompts to select one unless `--tenant` is provided.

**Note for agents**: This command is unavoidably interactive for the initial token exchange (requires browser). Run it once as a human. Tokens are stored in the OS keychain and auto-refresh before expiry.

```
xero auth login [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--tenant`, `-t` | TEXT | None | Tenant name (substring match) or exact tenant ID. Skips interactive org selection prompt. |

**Exit codes**: `0` on success, `1` on error or timeout (120 s).

**Output**:
```
Successfully authenticated! Connected to <Tenant Name>
```

---

### `xero auth status`

Show current authentication status.

**Interactive**: No

```
xero auth status
```

**Output**: Table with:
- Organization name
- Tenant ID
- Access token validity and expiration (UTC)

**Exit codes**: `0` if authenticated, `1` if not authenticated.

---

### `xero auth logout`

Remove stored credentials from the OS keychain.

**Interactive**: No

```
xero auth logout
```

**Output**: `Logged out. Credentials removed from keychain.`

---

## `xero invoices` — Invoice Management

### `xero invoices list`

List invoices with optional filters.

**Interactive**: No

```
xero invoices list [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--status` | `-s` | TEXT | None | Filter by status: `DRAFT`, `AUTHORISED`, `PAID`, `VOIDED` |
| `--contact` | `-c` | TEXT | None | Filter by contact name (case-insensitive substring match) |
| `--days` | `-d` | INT | `90` | Show invoices from last N days |
| `--limit` | `-l` | INT | `50` | Maximum number of invoices to show |

**Output**: Rich table — Invoice #, Date, Due Date, Contact, Status (color-coded), Amount Due, Total.

Status colors: DRAFT=yellow, SUBMITTED=blue, AUTHORISED=green, PAID=cyan, VOIDED=dim, DELETED=red.

**Exit codes**: `0` on success, `1` on API error.

---

### `xero invoices get <INVOICE_ID>`

Show detailed view of a single invoice.

**Interactive**: No

```
xero invoices get <INVOICE_ID>
```

| Argument | Required | Description |
|---|---|---|
| `INVOICE_ID` | Yes | Invoice ID (UUID) or invoice number (e.g. `INV-0042`) |

**Output**:
- Invoice detail table: Invoice #, Type, Status, Contact, Date, Due Date, Sub Total, Tax, Total, Amount Due
- Line items table (if present): Description, Qty, Unit Price, Account, Amount

**Exit codes**: `0` on success, `1` if not found or API error.

---

## `xero transactions` — Bank Transactions

### `xero transactions list`

List bank transactions.

**Interactive**: No

```
xero transactions list [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--days` | `-d` | INT | `30` | Show transactions from last N days |
| `--account` | `-a` | TEXT | None | Filter by bank account name (case-insensitive substring match) |
| `--unclassified` | `-u` | FLAG | `False` | Show only transactions without an account code |
| `--limit` | `-l` | INT | `50` | Maximum number of transactions to show |

**Output**: Rich table — Date, Description (truncated to 50 chars), Bank Account, Type, Account Code, Amount.

**Exit codes**: `0` on success, `1` on API error.

---

### `xero transactions classify`

AI-powered classification of unclassified bank transactions using Claude.

Fetches all `AUTHORISED` bank transactions with no account code on their line items, sends them to Claude in batches of 20, and optionally applies the suggested account codes back to Xero.

**Interactive**: Yes in default mode (prompts to confirm medium/low-confidence items). Use `--batch` or `--dry-run` for non-interactive operation.

```
xero transactions classify [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--days` | `-d` | INT | `30` | Classify transactions from last N days |
| `--dry-run` | | FLAG | `False` | Show suggestions without applying to Xero. **Non-interactive.** |
| `--batch` | | FLAG | `False` | Auto-apply all high-confidence classifications without confirmation. **Non-interactive.** |
| `--model` | `-m` | TEXT | `claude-sonnet-4-6` | Claude model to use for classification |

**Confidence levels**:
- `high` (green) — applied automatically in `--batch` mode
- `medium` (yellow) — requires confirmation in default mode
- `low` (red) — requires confirmation in default mode

**Output**: Classification results table — #, Date, Description, Amount, Suggested Account, Confidence, Reasoning. Followed by a summary: `N classified, N error(s)`.

**Exit codes**: `0` on success, `1` if `ANTHROPIC_API_KEY` not set or API error.

**Requirements**: `ANTHROPIC_API_KEY` must be set.

---

## `xero reports` — Financial Reports

### `xero reports profit-loss`

Generate a Profit & Loss report.

**Interactive**: No

```
xero reports profit-loss [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--months` | `-m` | INT | `12` | Number of months to report on (from today backwards) |
| `--from` | | TEXT (YYYY-MM-DD) | None | Start date. Overrides `--months`. |
| `--to` | | TEXT (YYYY-MM-DD) | None | End date. Defaults to today. |

**Output**: Hierarchical financial statement with sections (Income, Expenses, etc.), rows, and bold summary rows.

**Exit codes**: `0` on success, `1` on API error.

---

### `xero reports balance-sheet`

Generate a Balance Sheet report.

**Interactive**: No

```
xero reports balance-sheet [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--date` | TEXT (YYYY-MM-DD) | Today | Report as-of date |

**Output**: Hierarchical balance sheet with Assets, Liabilities, Equity sections.

**Exit codes**: `0` on success, `1` on API error.

---

### `xero reports aged-receivables`

Show Aged Receivables — outstanding invoices grouped by contact and aging bucket.

**Interactive**: No

```
xero reports aged-receivables [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--date` | TEXT (YYYY-MM-DD) | Today | Report as-of date |

**Output**: Aged receivables report showing contact names, invoice aging buckets, and totals.

**Exit codes**: `0` on success, `1` on API error.

---

## Token & Credential Management

Tokens are stored in the OS keychain (macOS Keychain / Linux Secret Service / Windows Credential Manager) under the service name `xero-cli`.

Tokens are automatically refreshed 5 minutes before expiry — no manual refresh needed.

Token data stored per session:
- `access_token`
- `refresh_token`
- `expires_at` (Unix timestamp)
- `tenant_id`
- `tenant_name`

---

## Xero API Details

- Base URL: `https://api.xero.com/api.xro/2.0`
- Auth: OAuth2 Bearer token
- Tenant header: `xero-tenant-id` (automatically included)
- HTTP client: `httpx`

---

## Non-Interactive Mode Summary

| Command | Non-Interactive? | Notes |
|---|---|---|
| `xero auth login` | Partial | Browser OAuth is unavoidable; use `--tenant` to skip org selection prompt |
| `xero auth status` | Yes | |
| `xero auth logout` | Yes | |
| `xero invoices list` | Yes | |
| `xero invoices get` | Yes | |
| `xero transactions list` | Yes | |
| `xero transactions classify --batch` | Yes | Auto-applies high-confidence only |
| `xero transactions classify --dry-run` | Yes | Read-only, no writes |
| `xero reports profit-loss` | Yes | |
| `xero reports balance-sheet` | Yes | |
| `xero reports aged-receivables` | Yes | |
