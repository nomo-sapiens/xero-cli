from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from xero_cli.auth.token_store import TokenStore


class TestTokenStore:
    def test_save_and_load(self, tmp_path):
        token_data = {"access_token": "abc", "expires_at": 9999999999.0}
        with patch("xero_cli.auth.token_store.keyring") as mock_keyring:
            store = TokenStore()
            store.save(token_data)
            mock_keyring.set_password.assert_called_once_with(
                "xero-cli", "tokens", json.dumps(token_data)
            )

            mock_keyring.get_password.return_value = json.dumps(token_data)
            result = store.load()
            assert result == token_data

    def test_load_returns_none_when_empty(self):
        with patch("xero_cli.auth.token_store.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = None
            store = TokenStore()
            assert store.load() is None

    def test_clear(self):
        with patch("xero_cli.auth.token_store.keyring") as mock_keyring:
            store = TokenStore()
            store.clear()
            mock_keyring.delete_password.assert_called_once_with("xero-cli", "tokens")

    def test_clear_ignores_missing(self):
        import keyring.errors

        with patch("xero_cli.auth.token_store.keyring") as mock_keyring:
            mock_keyring.errors = keyring.errors
            mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError("not found")
            store = TokenStore()
            store.clear()  # should not raise


class TestGetToken:
    def test_returns_valid_token(self, valid_token, mocker):
        mocker.patch("xero_cli.auth.client.TokenStore").return_value.load.return_value = valid_token
        from xero_cli.auth.client import get_token

        result = get_token()
        assert result["access_token"] == "test-access-token"

    def test_raises_exit_when_no_token(self, mocker):
        mocker.patch("xero_cli.auth.client.TokenStore").return_value.load.return_value = None
        from xero_cli.auth.client import get_token
        import typer

        with pytest.raises(SystemExit):
            get_token()

    def test_refreshes_expired_token(self, expired_token, valid_token, mocker):
        store_mock = MagicMock()
        store_mock.load.return_value = expired_token
        mocker.patch("xero_cli.auth.client.TokenStore", return_value=store_mock)

        new_token = {**valid_token, "access_token": "new-access-token"}
        mocker.patch("xero_cli.auth.client.refresh_token", return_value=new_token)
        mocker.patch("xero_cli.auth.client.get_settings")

        from xero_cli.auth.client import get_token

        result = get_token()
        assert result["access_token"] == "new-access-token"
        store_mock.save.assert_called_once_with(new_token)


class TestGetClient:
    def test_returns_httpx_client(self, valid_token, mocker):
        mocker.patch("xero_cli.auth.client.get_token", return_value=valid_token)
        from xero_cli.auth.client import get_client

        client = get_client()
        assert "Bearer test-access-token" in str(client.headers.get("authorization", ""))
        assert client.headers.get("xero-tenant-id") == "test-tenant-id"
