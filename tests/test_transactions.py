from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from xero_cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_tx_client(sample_transactions, mocker):
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"BankTransactions": sample_transactions}
    client.get.return_value = response
    mocker.patch("xero_cli.transactions.commands.get_client", return_value=client)
    return client


class TestTransactionsList:
    def test_lists_transactions(self, mock_tx_client):
        result = runner.invoke(app, ["transactions", "list"])
        assert result.exit_code == 0
        assert "WOOLWORTHS" in result.output

    def test_filters_by_account(self, mock_tx_client):
        result = runner.invoke(app, ["transactions", "list", "--account", "cheque"])
        assert result.exit_code == 0
        assert "WOOLWORTHS" in result.output

    def test_filters_unclassified(self, mock_tx_client):
        result = runner.invoke(app, ["transactions", "list", "--unclassified"])
        assert result.exit_code == 0
        # Both fixtures have empty AccountCode
        assert "WOOLWORTHS" in result.output

    def test_handles_api_error(self, mocker):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"
        client.get.return_value = response
        mocker.patch("xero_cli.transactions.commands.get_client", return_value=client)

        result = runner.invoke(app, ["transactions", "list"])
        assert result.exit_code != 0

    def test_shows_no_transactions_message(self, mocker):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"BankTransactions": []}
        client.get.return_value = response
        mocker.patch("xero_cli.transactions.commands.get_client", return_value=client)

        result = runner.invoke(app, ["transactions", "list"])
        assert result.exit_code == 0
        assert "No transactions found" in result.output


class TestTransactionsClassify:
    def test_requires_anthropic_key(self, mocker):
        mocker.patch(
            "xero_cli.transactions.commands.get_settings",
            return_value=MagicMock(anthropic_api_key=""),
        )
        mocker.patch("xero_cli.transactions.commands.get_client")
        mocker.patch("xero_cli.transactions.commands.get_token")

        result = runner.invoke(app, ["transactions", "classify"])
        assert result.exit_code != 0
        assert "ANTHROPIC_API_KEY" in result.output

    def test_dry_run_does_not_update(self, sample_transactions, sample_accounts, mocker):
        # Setup mocks
        client = MagicMock()
        tx_response = MagicMock()
        tx_response.status_code = 200
        tx_response.json.return_value = {"BankTransactions": sample_transactions}

        acct_response = MagicMock()
        acct_response.status_code = 200
        acct_response.json.return_value = {"Accounts": sample_accounts}

        client.get.side_effect = [tx_response, acct_response]
        mocker.patch("xero_cli.transactions.commands.get_client", return_value=client)
        mocker.patch("xero_cli.transactions.commands.get_token", return_value={"tenant_id": "t1"})
        mocker.patch(
            "xero_cli.transactions.commands.get_settings",
            return_value=MagicMock(anthropic_api_key="test-key"),
        )

        classifications = [
            {
                "transaction_id": "tx-001",
                "account_code": "420",
                "account_name": "Office Supplies",
                "confidence": "high",
                "reasoning": "supermarket",
            },
            {
                "transaction_id": "tx-002",
                "account_code": "460",
                "account_name": "Software / IT",
                "confidence": "high",
                "reasoning": "adobe",
            },
        ]
        mocker.patch(
            "xero_cli.transactions.commands.classify_transactions",
            return_value=classifications,
        )

        result = runner.invoke(app, ["transactions", "classify", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output
        # Should NOT have called client.post
        client.post.assert_not_called()

    def test_shows_all_transactions_classified(self, mocker):
        # All transactions already have account codes
        classified_txs = [
            {
                "BankTransactionID": "tx-001",
                "Status": "AUTHORISED",
                "DateString": "2024-03-15T00:00:00",
                "Reference": "WOOLWORTHS",
                "Total": -87.43,
                "BankAccount": {"Name": "Business Cheque"},
                "LineItems": [{"Description": "WOOLWORTHS", "AccountCode": "420"}],
            }
        ]
        client = MagicMock()
        tx_response = MagicMock()
        tx_response.status_code = 200
        tx_response.json.return_value = {"BankTransactions": classified_txs}
        client.get.return_value = tx_response

        mocker.patch("xero_cli.transactions.commands.get_client", return_value=client)
        mocker.patch("xero_cli.transactions.commands.get_token", return_value={"tenant_id": "t1"})
        mocker.patch(
            "xero_cli.transactions.commands.get_settings",
            return_value=MagicMock(anthropic_api_key="test-key"),
        )

        result = runner.invoke(app, ["transactions", "classify"])
        assert result.exit_code == 0
        assert "already classified" in result.output
