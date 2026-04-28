from __future__ import annotations

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
