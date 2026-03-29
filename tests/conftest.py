from __future__ import annotations

import json
import time
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def valid_token() -> dict:
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
        "expires_in": 1800,
        "expires_at": time.time() + 1800,
        "tenant_id": "test-tenant-id",
        "tenant_name": "Test Org",
    }


@pytest.fixture
def expired_token(valid_token: dict) -> dict:
    return {**valid_token, "expires_at": time.time() - 100}


@pytest.fixture
def mock_token_store(valid_token: dict, mocker):
    store = MagicMock()
    store.load.return_value = valid_token
    store.save.return_value = None
    store.clear.return_value = None
    mocker.patch("xero_cli.auth.client.TokenStore", return_value=store)
    mocker.patch("xero_cli.auth.commands.TokenStore", return_value=store)
    return store


@pytest.fixture
def sample_invoices() -> list[dict]:
    return [
        {
            "InvoiceID": "inv-001",
            "InvoiceNumber": "INV-0001",
            "Type": "ACCREC",
            "Status": "AUTHORISED",
            "Contact": {"Name": "Acme Corp"},
            "DateString": "2024-03-15T00:00:00",
            "DueDateString": "2024-04-15T00:00:00",
            "Total": 1500.00,
            "AmountDue": 1500.00,
            "SubTotal": 1363.64,
            "TotalTax": 136.36,
            "CurrencyCode": "AUD",
            "LineItems": [
                {
                    "Description": "Consulting services",
                    "Quantity": 10,
                    "UnitAmount": 136.364,
                    "AccountCode": "200",
                    "LineAmount": 1363.64,
                }
            ],
        },
        {
            "InvoiceID": "inv-002",
            "InvoiceNumber": "INV-0002",
            "Type": "ACCREC",
            "Status": "PAID",
            "Contact": {"Name": "Beta Ltd"},
            "DateString": "2024-03-10T00:00:00",
            "DueDateString": "2024-04-10T00:00:00",
            "Total": 500.00,
            "AmountDue": 0.00,
            "SubTotal": 454.55,
            "TotalTax": 45.45,
            "CurrencyCode": "AUD",
            "LineItems": [],
        },
    ]


@pytest.fixture
def sample_transactions() -> list[dict]:
    return [
        {
            "BankTransactionID": "tx-001",
            "Type": "SPEND",
            "Status": "AUTHORISED",
            "DateString": "2024-03-15T00:00:00",
            "Reference": "WOOLWORTHS SYDNEY",
            "Total": -87.43,
            "BankAccount": {"Name": "Business Cheque"},
            "LineItems": [{"Description": "WOOLWORTHS SYDNEY", "AccountCode": ""}],
        },
        {
            "BankTransactionID": "tx-002",
            "Type": "SPEND",
            "Status": "AUTHORISED",
            "DateString": "2024-03-14T00:00:00",
            "Reference": "ADOBE INC",
            "Total": -54.99,
            "BankAccount": {"Name": "Business Cheque"},
            "LineItems": [{"Description": "ADOBE INC", "AccountCode": ""}],
        },
    ]


@pytest.fixture
def sample_accounts() -> list[dict]:
    return [
        {"AccountID": "acc-001", "Code": "200", "Name": "Sales", "Type": "REVENUE", "Status": "ACTIVE"},
        {"AccountID": "acc-002", "Code": "400", "Name": "Advertising", "Type": "EXPENSE", "Status": "ACTIVE"},
        {"AccountID": "acc-003", "Code": "420", "Name": "Office Supplies", "Type": "EXPENSE", "Status": "ACTIVE"},
        {"AccountID": "acc-004", "Code": "460", "Name": "Software / IT", "Type": "EXPENSE", "Status": "ACTIVE"},
        {"AccountID": "acc-005", "Code": "310", "Name": "Meals & Entertainment", "Type": "EXPENSE", "Status": "ACTIVE"},
    ]
