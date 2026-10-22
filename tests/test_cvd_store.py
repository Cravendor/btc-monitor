import json
import tempfile
import unittest
from pathlib import Path
from scripts.cvd_store import connect, record_trade, record_gap, export_health

class StoreTests(unittest.TestCase):
    def test_duplicate_and_gap_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = connect(Path(tmp) / "cvd.sqlite3")
            args = dict(market="spot", trade_id="1", ts_ms=1000,
                        received_ms=1100, price="80000", size_btc="0.1",
                        taker_side="buy")
            self.assertTrue(record_trade(db, **args))
            self.assertFalse(record_trade(db, **args))
            record_gap(db, market="spot", start_ms=1200, reason="disconnected")
            output = Path(tmp) / "health.json"
            result = export_health(db, output)
            self.assertEqual(result["markets"]["spot"]["trade_count"], 1)
            self.assertEqual(result["markets"]["spot"]["unresolved_gaps"], 1)
            self.assertFalse(result["markets"]["spot"]["coverage_verified"])
            self.assertIsNone(json.loads(output.read_text())["cvd_4h"])
            db.close()

    def test_invalid_side(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = connect(Path(tmp) / "cvd.sqlite3")
            with self.assertRaises(ValueError):
                record_trade(db, market="spot", trade_id="2", ts_ms=1,
                             received_ms=2, price="1", size_btc="1", taker_side="unknown")
            db.close()
