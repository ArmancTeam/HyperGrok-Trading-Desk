#!/usr/bin/env python3
import sys, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_quality_guard import validate_snapshot, require_accepted

class Tests(unittest.TestCase):
    now = datetime(2026, 11, 9, 18, 0, tzinfo=timezone.utc)
    def quote(self):
        return {"source":"MEXC","symbol":"BTCUSDT","market_type":"spot",
          "observed_at":"2026-11-09T18:00:00Z","bid":"99900","ask":"100100","last":"100000"}
    def test_fresh(self):
        self.assertTrue(validate_snapshot(self.quote(), now=self.now,
            expected_source="MEXC", expected_market_type="spot").accepted)
    def test_stale(self):
        q=self.quote(); q["observed_at"]="2026-11-09T17:58:00Z"
        self.assertIn("stale_data", validate_snapshot(q, now=self.now).reasons)
    def test_missing(self):
        q=self.quote(); del q["bid"]
        self.assertIn("invalid_bid", validate_snapshot(q, now=self.now).reasons)
    def test_wrong_source(self):
        self.assertIn("source_mismatch", validate_snapshot(self.quote(), now=self.now,
            expected_source="Hyperliquid").reasons)
    def test_spot_perp_mismatch(self):
        self.assertIn("market_type_mismatch", validate_snapshot(self.quote(), now=self.now,
            expected_market_type="perpetual").reasons)
    def test_crossed_book(self):
        q=self.quote(); q["bid"],q["ask"]="100100","99900"
        self.assertIn("crossed_or_locked_book", validate_snapshot(q, now=self.now).reasons)
    def test_outlier(self):
        q=self.quote(); q["last"]="130000"
        self.assertIn("last_price_outlier", validate_snapshot(q, now=self.now).reasons)
    def test_fail_closed(self):
        q=self.quote(); q["observed_at"]="2026-11-09T17:00:00Z"
        with self.assertRaises(ValueError): require_accepted(validate_snapshot(q, now=self.now))

if __name__ == "__main__": unittest.main(verbosity=2)
