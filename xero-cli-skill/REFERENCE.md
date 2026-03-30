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

## `xero accounts` — Chart of Accounts

### `xero accounts list`

List the chart of accounts.

**Interactive**: No

```
xero accounts list [OPTIONS]
```

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--type` | `-t` | TEXT | None | Filter by account type (e.g. `EXPENSE`, `REVENUE`, `ASSET`, `LIABILITY`) |
| `--status` | `-s` | TEXT | None | Filter by status: `ACTIVE`, `ARCHIVED` |

**Output**: Table — Code, Name, Type, Tax Type, Status. Sorted by account code.

**Exit codes**: `0` on success, `1` on API error.

---

### `xero accounts add`

Add a new account to the chart of accounts.

**Interactive**: No

```
xero accounts add --name <NAME> --type <TYPE> [OPTIONS]
```

| Option | Short | Type | Required | Description |
|---|---|---|---|---|
| `--name` | `-n` | TEXT | Yes | Account name (e.g. `Office Expenses`) |
| `--type` | `-t` | TEXT | Yes | Account type: `EXPENSE`, `REVENUE`, `ASSET`, `LIABILITY`, `EQUITY`, `BANK` |
| `--code` | `-c` | TEXT | No | Account code (e.g. `420`) |
| `--tax-type` | | TEXT | No | Tax type (e.g. `INPUT`, `OUTPUT`, `NONE`) |
| `--description` | `-d` | TEXT | No | Account description |

**Common account types**:

| Type | Use for |
|---|---|
| `EXPENSE` | Money spent running the business (office supplies, software, travel) |
| `REVENUE` | Income from business activities |
| `ASSET` | Things the business owns (equipment, investments) |
| `LIABILITY` | Money owed by the business |
| `EQUITY` | Owner's stake in the business |
| `BANK` | Bank or credit card accounts |

**Output**: `Created: <code>  <name>  (<type>)`

**Exit codes**: `0` on success, `1` on API error.

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

### Agent-driven transaction classification

Classification is performed by the agent using the following CLI commands:

```bash
xero transactions list --unclassified --days N   # get transactions to classify
xero accounts list                                # get valid account codes
xero transactions set-account <id> <code>        # apply a single classification
```

The agent reasons about each transaction, presents a proposed classification table, **confirms with the user**, then applies approved items one by one using `set-account`.

**Confidence levels**:

| Level | Colour | Behaviour |
|---|---|---|
| `high` | green | Agent recommends applying — still requires user confirmation |
| `medium` | yellow | Agent flags as uncertain — confirm before applying |
| `low` | red | Agent skips unless user explicitly requests |

**Summary output**: `N applied, N skipped, N error(s)`.

---

### `xero transactions set-account`

Set the account code on a single bank transaction.

**Interactive**: No

```
xero transactions set-account <TRANSACTION_ID> <ACCOUNT_CODE>
```

| Argument | Required | Description |
|---|---|---|
| `TRANSACTION_ID` | Yes | BankTransactionID (UUID) — shown in `xero transactions list` output |
| `ACCOUNT_CODE` | Yes | Account code to assign (e.g. `420`) — see `xero accounts list` |

**Output**: `Updated: <description> → account code <code>`

**Exit codes**: `0` on success, `1` if transaction not found or API error.

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
| `xero accounts list` | Yes | |
| `xero accounts add` | Yes | |
| `xero transactions list` | Yes | |
| `xero transactions set-account` | Yes | Applies a single classification |
| Agent classification | Yes | Agent reasons, presents table, confirms with user, then applies via `set-account` |
| `xero reports profit-loss` | Yes | |
| `xero reports balance-sheet` | Yes | |
| `xero reports aged-receivables` | Yes | |
