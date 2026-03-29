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
    "accounting.transactions",
    "accounting.transactions.read",
    "accounting.reports.read",
    "accounting.settings",
    "accounting.settings.read",
    "offline_access",
]


@dataclass
class Settings:
    client_id: str
    client_secret: str
    anthropic_api_key: str = ""
    redirect_uri: str = "http://localhost:8080/callback"
    scopes: list[str] = field(default_factory=lambda: list(XERO_SCOPES))


def get_settings() -> Settings:
    """Load settings from environment variables, then config file as fallback."""
    client_id = os.environ.get("XERO_CLIENT_ID", "")
    client_secret = os.environ.get("XERO_CLIENT_SECRET", "")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        if not client_id:
            client_id = config.get("client_id", "")
        if not client_secret:
            client_secret = config.get("client_secret", "")
        if not anthropic_api_key:
            anthropic_api_key = config.get("anthropic_api_key", "")

    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        anthropic_api_key=anthropic_api_key,
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
