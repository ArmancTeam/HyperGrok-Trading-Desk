import unittest
from unittest.mock import patch

import mexc_account


class MexcAccountTests(unittest.TestCase):
    def test_spot_returns_nonzero_balances(self):
        payload = {
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.1"},
                {"asset": "USDT", "free": "0", "locked": "0"},
            ]
        }

        with patch.object(mexc_account, "signed_spot_get", return_value=payload):
            result = mexc_account.read_spot("key", "secret")

        self.assertEqual(len(result["balances"]), 1)
        self.assertEqual(result["balances"][0]["asset"], "BTC")
        self.assertEqual(result["balances"][0]["total"], "0.6")

    def test_spot_rejects_negative_balance(self):
        payload = {
            "balances": [
                {"asset": "BTC", "free": "-1", "locked": "0"}
            ]
        }

        with patch.object(mexc_account, "signed_spot_get", return_value=payload):
            with self.assertRaises(mexc_account.MexcAuthError):
                mexc_account.read_spot("key", "secret")

    def test_futures_accepts_negative_unrealized_pnl(self):
        payload = {
            "success": True,
            "data": {
                "currency": "USDT",
                "availableBalance": "100",
                "cashBalance": "100",
                "frozenBalance": "0",
                "equity": "98.75",
                "unrealized": "-1.25",
                "positionMargin": "0",
            },
        }

        with patch.object(
            mexc_account, "signed_futures_get", return_value=payload
        ):
            result = mexc_account.read_futures("key", "secret")

        self.assertEqual(result["balance"]["unrealized"], "-1.25")

    def test_futures_rejects_negative_available_balance(self):
        payload = {
            "success": True,
            "data": {
                "currency": "USDT",
                "availableBalance": "-1",
                "cashBalance": "100",
                "frozenBalance": "0",
                "equity": "100",
                "unrealized": "0",
                "positionMargin": "0",
            },
        }

        with patch.object(
            mexc_account, "signed_futures_get", return_value=payload
        ):
            with self.assertRaises(mexc_account.MexcAuthError):
                mexc_account.read_futures("key", "secret")

    def test_futures_rejects_currency_mismatch(self):
        payload = {
            "success": True,
            "data": {"currency": "BTC"},
        }

        with patch.object(
            mexc_account, "signed_futures_get", return_value=payload
        ):
            with self.assertRaises(mexc_account.MexcAuthError):
                mexc_account.read_futures("key", "secret", "USDT")


if __name__ == "__main__":
    unittest.main()
