from __future__ import annotations

import json
from typing import Any

import keyring
import keyring.errors

SERVICE_NAME = "xero-cli"
TOKEN_KEY = "tokens"


class TokenStore:
    def save(self, token_data: dict[str, Any]) -> None:
        keyring.set_password(SERVICE_NAME, TOKEN_KEY, json.dumps(token_data))

    def load(self) -> dict[str, Any] | None:
        raw = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
        if not raw:
            return None
        return json.loads(raw)

    def clear(self) -> None:
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
        except keyring.errors.PasswordDeleteError:
            pass
