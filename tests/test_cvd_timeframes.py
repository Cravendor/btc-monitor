import tempfile
import unittest
from pathlib import Path
from scripts.cvd_store import connect, record_trade, record_gap
from scripts.cvd_timeframes import aligned_start, observed_window, latest_closed_windows

class TimeframeTests(unittest.TestCase):
    def test_alignment(self):
        self.assertEqual(aligned_start(300001, "5m"), 300000)
        self.assertEqual(aligned_start(4*86400000, "1w"), 4*86400000)
        self.assertEqual(aligned_start(0, "1w"), -3*86400000)

    def test_delta_never_claims_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = connect(Path(tmp) / "db.sqlite")
            for i, side in enumerate(("buy", "sell")):
                record_trade(db, market="spot", trade_id=str(i),
                             ts_ms=1000+i, received_ms=1100+i,
                             price="80000", size_btc="0.2" if i == 0 else "0.1",
                             taker_side=side)
            record_gap(db, market="spot", start_ms=2000, end_ms=3000,
                       reason="disconnect")
            result = observed_window(db, "spot", "1m", 0, now_ms=120000)
            self.assertEqual(result["observed_delta_btc"], "0.1")
            self.assertEqual(result["unresolved_gaps"], 1)
            self.assertIsNone(result["cvd"])
            self.assertFalse(result["coverage_verified"])
            self.assertEqual(result["status"], "incomplete")
            db.close()
