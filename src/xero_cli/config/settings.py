from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import tomli_w
from dotenv import load_dotenv
from platformdirs import user_config_dir

load_dotenv()

CONFIG_DIR = Path(user_config_dir("xero-cli"))
CONFIG_FILE = CONFIG_DIR / "config.toml"

XERO_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "accounting.settings",                   # /Accounts
    "accounting.invoices",                   # /Invoices
    "accounting.banktransactions",           # /BankTransactions
    "accounting.reports.profitandloss.read", # /Reports/ProfitAndLoss
    "accounting.reports.balancesheet.read",  # /Reports/BalanceSheet
    "accounting.reports.aged.read",          # /Reports/AgedReceivablesByContact
]


@dataclass
class Settings:
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/callback"
    scopes: list[str] = field(default_factory=lambda: list(XERO_SCOPES))


def get_settings() -> Settings:
    """Load settings from environment variables, then config file as fallback."""
    client_id = os.environ.get("XERO_CLIENT_ID", "")
    client_secret = os.environ.get("XERO_CLIENT_SECRET", "")

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        if not client_id:
            client_id = config.get("client_id", "")
        if not client_secret:
            client_secret = config.get("client_secret", "")
    return Settings(
        client_id=client_id,
        client_secret=client_secret,
    )


def save_config(data: dict) -> None:
    """Merge data into the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            existing = tomllib.load(f)
    existing.update(data)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(existing, f)
