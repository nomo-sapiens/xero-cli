# xero-cli

An AI-powered command-line tool for managing your Xero accounting. Classify bank transactions with Claude, view invoices, check reports — all from the terminal.

## Features

- **AI transaction classification** — uses Claude to suggest account codes for unclassified bank transactions, with interactive confirmation or batch mode
- **Invoices** — list, filter, and inspect invoices
- **Bank transactions** — browse and filter transactions by account or date range
- **Reports** — Profit & Loss, Balance Sheet, and Aged Receivables

## Requirements

- Python 3.11+
- A [Xero developer account](https://developer.xero.com) with an OAuth2 app
- An [Anthropic API key](https://console.anthropic.com) (for AI classification)

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
3. Set the **Redirect URI** to `http://localhost:8080/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Configure credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Alternatively, export the variables in your shell or store them in `~/.config/xero-cli/config.toml`:

```toml
client_id = "your_client_id"
client_secret = "your_client_secret"
anthropic_api_key = "your_key"
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

### Bank Transactions

```bash
# List transactions from the last 30 days
xero transactions list

# Show last 90 days
xero transactions list --days 90

# Filter by bank account
xero transactions list --account "Business Cheque"

# Show only unclassified transactions
xero transactions list --unclassified
```

### AI Transaction Classification

Classify unclassified bank transactions using Claude:

```bash
# Interactive mode — review and confirm each suggestion
xero transactions classify

# Dry run — see suggestions without applying them
xero transactions classify --dry-run

# Batch mode — auto-apply all high-confidence suggestions
xero transactions classify --batch

# Classify transactions from the last 90 days
xero transactions classify --days 90

# Use a specific Claude model
xero transactions classify --model claude-opus-4-6
```

**How it works:**

1. Fetches all unclassified transactions (those without an account code) from Xero
2. Loads your chart of accounts
3. Sends transactions to Claude in batches of 20
4. Claude suggests an account code, confidence level, and brief reasoning for each transaction
5. In interactive mode, you confirm each suggestion; in `--batch` mode, high-confidence suggestions are applied automatically

Example output:

```
Classification Results
──────────────────────────────────────────────────────────────────
 #   Date        Description              Amount     Suggested Account         Conf   Reasoning
 1   2024-03-15  WOOLWORTHS SYDNEY       -87.43     420 - Office Supplies     high   Supermarket purchase
 2   2024-03-14  ADOBE INC              -54.99     460 - Software / IT        high   Software subscription
 3   2024-03-13  CASH WITHDRAWAL       -200.00     —                          low    Cannot determine
──────────────────────────────────────────────────────────────────
```

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
