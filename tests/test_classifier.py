from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from xero_cli.transactions.classifier import _get_description, classify_transactions


class TestGetDescription:
    def test_uses_line_item_description(self):
        tx = {"LineItems": [{"Description": "Adobe Creative Cloud"}], "Reference": "ADOBE"}
        assert _get_description(tx) == "Adobe Creative Cloud"

    def test_falls_back_to_reference(self):
        tx = {"LineItems": [{"Description": ""}], "Reference": "WOOLWORTHS 1234"}
        assert _get_description(tx) == "WOOLWORTHS 1234"

    def test_falls_back_to_id(self):
        tx = {"LineItems": [], "BankTransactionID": "abc-123"}
        assert _get_description(tx) == "abc-123"

    def test_truncates_long_reference(self):
        tx = {"LineItems": [], "Reference": "X" * 200, "BankTransactionID": "id"}
        result = _get_description(tx)
        assert len(result) <= 120


class TestClassifyTransactions:
    def test_classifies_transactions(self, sample_transactions, sample_accounts):
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    [
                        {
                            "transaction_id": "tx-001",
                            "account_code": "420",
                            "account_name": "Office Supplies",
                            "confidence": "high",
                            "reasoning": "Supermarket purchase likely office supplies",
                        },
                        {
                            "transaction_id": "tx-002",
                            "account_code": "460",
                            "account_name": "Software / IT",
                            "confidence": "high",
                            "reasoning": "Adobe is a software company",
                        },
                    ]
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("xero_cli.transactions.classifier.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = mock_client
            results = classify_transactions(
                sample_transactions,
                sample_accounts,
                anthropic_api_key="test-key",
            )

        assert len(results) == 2
        assert results[0]["account_code"] == "420"
        assert results[1]["account_code"] == "460"
        assert results[0]["confidence"] == "high"

    def test_handles_markdown_code_fences(self, sample_transactions, sample_accounts):
        classification = [
            {
                "transaction_id": "tx-001",
                "account_code": "420",
                "account_name": "Office Supplies",
                "confidence": "high",
                "reasoning": "test",
            },
            {
                "transaction_id": "tx-002",
                "account_code": "460",
                "account_name": "Software / IT",
                "confidence": "high",
                "reasoning": "test",
            },
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=f"```json\n{json.dumps(classification)}\n```")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("xero_cli.transactions.classifier.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = mock_client
            results = classify_transactions(
                sample_transactions,
                sample_accounts,
                anthropic_api_key="test-key",
            )

        assert results[0]["account_code"] == "420"

    def test_handles_api_failure_gracefully(self, sample_transactions, sample_accounts):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json {{{")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("xero_cli.transactions.classifier.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = mock_client
            results = classify_transactions(
                sample_transactions,
                sample_accounts,
                anthropic_api_key="test-key",
            )

        # Should return low-confidence unknowns, not raise
        assert len(results) == 2
        for r in results:
            assert r["confidence"] == "low"
            assert r["account_code"] == ""

    def test_batches_large_input(self, sample_accounts):
        transactions = [
            {
                "BankTransactionID": f"tx-{i:03d}",
                "DateString": "2024-03-01T00:00:00",
                "Reference": f"SHOP {i}",
                "Total": -10.00 * i,
                "Type": "SPEND",
                "LineItems": [{"Description": f"Purchase {i}", "AccountCode": ""}],
            }
            for i in range(45)
        ]

        def make_result(batch):
            return [
                {
                    "transaction_id": tx["BankTransactionID"],
                    "account_code": "420",
                    "account_name": "Office Supplies",
                    "confidence": "high",
                    "reasoning": "test",
                }
                for tx in batch
            ]

        mock_client = MagicMock()
        responses = [
            MagicMock(content=[MagicMock(text=json.dumps(make_result(transactions[i : i + 20])))])
            for i in range(0, 45, 20)
        ]
        mock_client.messages.create.side_effect = responses

        with patch("xero_cli.transactions.classifier.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = mock_client
            results = classify_transactions(
                transactions,
                sample_accounts,
                anthropic_api_key="test-key",
                batch_size=20,
            )

        # 45 transactions / 20 per batch = 3 batches
        assert mock_client.messages.create.call_count == 3
        assert len(results) == 45
