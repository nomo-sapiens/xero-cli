# xero-cli

A command-line tool for managing your Xero accounting. View invoices, classify transactions, check reports — all from the terminal. Designed to be used with an AI agent (Claude Code + the included skill) for automated transaction classification.

## Features

- **Accounts** — browse your chart of accounts
- **Invoices** — list, filter, and inspect invoices
- **Bank transactions** — browse, filter, and set account codes on transactions
- **Reports** — Profit & Loss, Balance Sheet, and Aged Receivables
- **Agent-ready** — includes a Claude Code skill for AI-driven transaction classification (see `xero-cli-skill/`)

## Requirements

- Python 3.11+
- A [Xero developer account](https://developer.xero.com) with an OAuth2 app

## Installation

```bash
pip install xero-cli
```

Or install from source:

```bash
git clone https://github.com/dirkbrand/xero-cli
cd xero-cli
pip install -e ".[dev]"
```

## Setup

### 1. Create a Xero OAuth2 app

1. Go to [developer.xero.com/app/manage](https://developer.xero.com/app/manage)
2. Click **New app**
3. Select **Web app** as the app type (required — other types don't support the authorization code flow)
4. Set the **Redirect URI** to `http://localhost:8080/callback`
5. Note your **Client ID** and **Client Secret**

> **Note:** If you see `unauthorized_client: Invalid scope` during login, check that your app type is **Web app**. Xero migrated to granular scopes in March 2026 — apps created after that date require the new scope names, which this CLI uses automatically.

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
```

Alternatively, export the variables in your shell or store them in `~/.config/xero-cli/config.toml`:

```toml
client_id = "your_client_id"
client_secret = "your_client_secret"
```

### 3. Authenticate

```bash
xero auth login

# If you have multiple Xero organizations, auto-select one to skip the prompt:
xero auth login --tenant "Acme Ltd"
```

This opens a browser window. After authorizing, credentials are stored securely in your OS keychain (macOS Keychain / Linux Secret Service / Windows Credential Store).

Check status at any time:

```bash
xero auth status
```

## Usage

### Authentication

```bash
xero auth login                    # Authenticate with Xero
xero auth login --tenant "Acme"   # Auto-select org by name (non-interactive)
xero auth status                   # Show current auth status and token expiry
xero auth logout                   # Remove stored credentials
```

### Invoices

```bash
# List recent invoices
xero invoices list

# Filter by status
xero invoices list --status AUTHORISED
xero invoices list --status PAID

# Filter by contact name
xero invoices list --contact "Acme"

# Show invoices from the last 7 days
xero invoices list --days 7

# Get details for a specific invoice
xero invoices get INV-0042
```

### Chart of Accounts

```bash
# List all accounts
xero accounts list

# Filter by type
xero accounts list --type EXPENSE
xero accounts list --type REVENUE

# Show only active accounts
xero accounts list --status ACTIVE

# Add a new account
xero accounts add --name "Office Expenses" --type EXPENSE --code 420
xero accounts add --name "Software & Subscriptions" --type EXPENSE --code 460
xero accounts add --name "Investments" --type ASSET --code 710
```

### Bank Transactions

```bash
# List transactions from the last 30 days
xero transactions list

# Show last 90 days
xero transactions list --days 90

# Filter by bank account
xero transactions list --account "Business Cheque"

# Show only unclassified transactions (includes Transaction IDs for set-account)
xero transactions list --unclassified

# Set an account code on a transaction
xero transactions set-account <transaction_id> <account_code>
```

### AI Transaction Classification (via Claude Code)

Transaction classification is handled by the Claude Code agent using the skill in `xero-cli-skill/`. The agent:

1. Fetches unclassified transactions with `xero transactions list --unclassified`
2. Loads the chart of accounts with `xero accounts list`
3. Reasons about each transaction and assigns a confidence level (high / medium / low)
4. Presents a proposed classification table and **waits for your confirmation**
5. Applies approved classifications with `xero transactions set-account`

Example proposed classification output:

```
 #   Transaction ID                        Date        Description        Amount    Suggested Account      Conf    Reasoning
 1   a1b2c3d4-...                          2024-03-15  WOOLWORTHS         -87.43    420 - Office Supplies  high    Supermarket
 2   e5f6g7h8-...                          2024-03-14  ADOBE INC          -54.99    460 - Software / IT    high    Subscription
 3   i9j0k1l2-...                          2024-03-13  CASH WITHDRAWAL   -200.00    —                      low     Insufficient context
```

To use: open Claude Code and invoke the `xero` skill, then ask it to classify your transactions.

### Reports

```bash
# Profit & Loss for the last 12 months
xero reports profit-loss

# P&L for a custom date range
xero reports profit-loss --from 2024-01-01 --to 2024-12-31

# Balance Sheet
xero reports balance-sheet
xero reports balance-sheet --date 2024-06-30

# Aged Receivables
xero reports aged-receivables
```

## Publishing a New Release

Tag a commit to trigger the GitHub Actions publish workflow:

```bash
git tag v0.2.0
git push origin v0.2.0
```

This will:
1. Build the distribution
2. Publish to TestPyPI
3. Publish to PyPI
4. Create a GitHub Release

### PyPI Setup

Before publishing, configure trusted publishing in PyPI:

1. Go to your PyPI project → **Publishing** → **Add a new publisher**
2. Set workflow filename: `publish.yml`
3. Set environment name: `pypi`

Repeat for TestPyPI with environment name `testpypi`.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=xero_cli

# Lint
ruff check src tests
ruff format src tests
```

## License

MIT
