import unittest
from unittest.mock import patch

from mexc_common import MexcPublicError
from mexc_spot import run_snapshot

TICKER = {
    "symbol": "BTCUSDT", "lastPrice": "75000",
    "priceChangePercent": "1.2", "volume": "100",
    "quoteVolume": "7500000", "highPrice": "76000",
    "lowPrice": "74000",
}
BOOK = {
    "symbol": "BTCUSDT", "bidPrice": "74999",
    "bidQty": "1.5", "askPrice": "75001", "askQty": "2",
}
DEPTH = {
    "timestamp": 1794270000000,
    "bids": [["74999", "1.5"]],
    "asks": [["75001", "2"]],
}


class MexcSpotTests(unittest.TestCase):

    @patch("mexc_spot.public_get")
    def test_valid_snapshot(self, mocked):
        mocked.side_effect = [TICKER, BOOK, DEPTH]
        result = run_snapshot()
        self.assertEqual(result["source"], "MEXC")
        self.assertEqual(result["market_type"], "spot")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["last"], "75000")
        self.assertFalse(result["permissions"]["account_access"])
        self.assertFalse(result["permissions"]["order_writes"])
        self.assertEqual(mocked.call_count, 3)

    @patch("mexc_spot.public_get")
    def test_accepts_negative_24h_change(self, mocked):
        negative_ticker = dict(TICKER, priceChangePercent="-0.0035")
        mocked.side_effect = [negative_ticker, BOOK, DEPTH]

        result = run_snapshot()

        self.assertEqual(result["change_percent_24h"], "-0.0035")

    @patch("mexc_spot.public_get")
    def test_rejects_crossed_book(self, mocked):
        crossed = dict(BOOK, bidPrice="75002", askPrice="75001")
        mocked.side_effect = [TICKER, crossed, DEPTH]
        with self.assertRaises(MexcPublicError):
            run_snapshot()

    @patch("mexc_spot.public_get")
    def test_rejects_empty_depth(self, mocked):
        mocked.side_effect = [TICKER, BOOK, {
            "timestamp": 1794270000000, "bids": [], "asks": []
        }]
        with self.assertRaises(MexcPublicError):
            run_snapshot()

    @patch("mexc_spot.public_get")
    def test_rejects_symbol_mismatch(self, mocked):
        mocked.side_effect = [dict(TICKER, symbol="ETHUSDT"), BOOK, DEPTH]
        with self.assertRaises(MexcPublicError):
            run_snapshot()

    def test_rejects_invalid_depth_limit(self):
        with self.assertRaises(MexcPublicError):
            run_snapshot(depth_limit=7)


if __name__ == "__main__":
    unittest.main()
