import unittest
from unittest.mock import patch

from mexc_common import MexcPublicError
from mexc_futures import run_snapshot


TICKER = {
    "symbol": "BTC_USDT",
    "bid1": "74999",
    "ask1": "75001",
    "lastPrice": "75000",
    "fairPrice": "75000",
    "indexPrice": "74998",
    "holdVol": "1000",
    "volume24": "2000",
    "amount24": "150000000",
}

DEPTH = {
    "timestamp": 1794270000000,
    "bids": [["74999", "1.5"]],
    "asks": [["75001", "2"]],
}

FUNDING = {
    "fundingRate": "0.0001",
    "nextSettleTime": 1794273600000,
}


class MexcFuturesTests(unittest.TestCase):

    @patch("mexc_futures.public_get")
    def test_valid_snapshot(self, mocked):
        mocked.side_effect = [TICKER, DEPTH, FUNDING]
        result = run_snapshot()

        self.assertEqual(result["source"], "MEXC")
        self.assertEqual(result["market_type"], "perpetual")
        self.assertEqual(result["symbol"], "BTC_USDT")
        self.assertEqual(result["last"], "75000")
        self.assertEqual(result["funding_rate"], "0.0001")
        self.assertFalse(result["permissions"]["account_access"])
        self.assertFalse(result["permissions"]["order_writes"])
        self.assertEqual(mocked.call_count, 3)

    @patch("mexc_futures.public_get")
    def test_rejects_crossed_book(self, mocked):
        crossed = dict(TICKER, bid1="75002", ask1="75001")
        mocked.side_effect = [crossed, DEPTH, FUNDING]

        with self.assertRaises(MexcPublicError):
            run_snapshot()

    @patch("mexc_futures.public_get")
    def test_rejects_empty_depth(self, mocked):
        empty = {
            "timestamp": 1794270000000,
            "bids": [],
            "asks": [],
        }
        mocked.side_effect = [TICKER, empty, FUNDING]

        with self.assertRaises(MexcPublicError):
            run_snapshot()

    @patch("mexc_futures.public_get")
    def test_rejects_symbol_mismatch(self, mocked):
        wrong = dict(TICKER, symbol="ETH_USDT")
        mocked.side_effect = [wrong, DEPTH, FUNDING]

        with self.assertRaises(MexcPublicError):
            run_snapshot()

    def test_rejects_invalid_symbol(self):
        with self.assertRaises(MexcPublicError):
            run_snapshot("BTCUSDT")

    def test_rejects_invalid_depth_limit(self):
        with self.assertRaises(MexcPublicError):
            run_snapshot(depth_limit=7)


if __name__ == "__main__":
    unittest.main()
