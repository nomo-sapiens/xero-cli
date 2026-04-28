from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from xero_cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_client(sample_invoices, mocker):
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"Invoices": sample_invoices}
    client.get.return_value = response
    mocker.patch("xero_cli.invoices.commands.get_client", return_value=client)
    return client


class TestInvoicesList:
    def test_lists_invoices(self, mock_client):
        result = runner.invoke(app, ["invoices", "list"])
        assert result.exit_code == 0
        assert "INV-0001" in result.output
        assert "Acme Corp" in result.output

    def test_filters_by_contact(self, mock_client):
        result = runner.invoke(app, ["invoices", "list", "--contact", "acme"])
        assert result.exit_code == 0
        assert "Acme Corp" in result.output
        assert "Beta Ltd" not in result.output

    def test_shows_no_invoices_message(self, mocker):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"Invoices": []}
        client.get.return_value = response
        mocker.patch("xero_cli.invoices.commands.get_client", return_value=client)

        result = runner.invoke(app, ["invoices", "list"])
        assert result.exit_code == 0
        assert "No invoices found" in result.output

    def test_handles_api_error(self, mocker):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 403
        response.text = "Forbidden"
        client.get.return_value = response
        mocker.patch("xero_cli.invoices.commands.get_client", return_value=client)

        result = runner.invoke(app, ["invoices", "list"])
        assert result.exit_code != 0
        assert "403" in result.output

    def test_respects_limit(self, mock_client, sample_invoices):
        result = runner.invoke(app, ["invoices", "list", "--limit", "1"])
        assert result.exit_code == 0
        # Only first invoice should appear
        assert "INV-0001" in result.output


class TestInvoiceGet:
    def test_gets_single_invoice(self, mocker, sample_invoices):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"Invoices": [sample_invoices[0]]}
        client.get.return_value = response
        mocker.patch("xero_cli.invoices.commands.get_client", return_value=client)

        result = runner.invoke(app, ["invoices", "get", "inv-001"])
        assert result.exit_code == 0
        assert "INV-0001" in result.output
        assert "Acme Corp" in result.output
        assert "1,500.00" in result.output

    def test_handles_not_found(self, mocker):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"Invoices": []}
        client.get.return_value = response
        mocker.patch("xero_cli.invoices.commands.get_client", return_value=client)

        result = runner.invoke(app, ["invoices", "get", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output
