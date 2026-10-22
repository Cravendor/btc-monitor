import json
import tempfile
import unittest
from pathlib import Path
from scripts.timeframe_signal_history import record_health, TIMEFRAMES


class TimeframeSignalHistoryTests(unittest.TestCase):
    def test_append_deduplicated_and_missing_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "signals.jsonl"
            health = {"exchange": "bitget", "market": "USDT-FUTURES",
                      "symbol": "BTCUSDT", "updated_at": "2026-10-22T17:00:00+00:00",
                      "timeframes": {"5m": {"status": "ok", "signal_status": "provisional",
                                             "grade": "slightly_bullish", "observed_at": "2026-10-22T16:55:00+00:00"},
                                     "1w": {"status": "error", "signal_status": "unavailable", "grade": None}}}
            record_health(health, path)
            record_health(health, path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(set(rows[0]["signals"]), set(TIMEFRAMES))
            self.assertEqual(rows[0]["signals"]["5m"]["grade"], "slightly_bullish")
            self.assertEqual(rows[0]["signals"]["1w"]["status"], "unavailable")

    def test_market_identity_required(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                record_health({"updated_at": "2026-10-22"}, Path(temp) / "x.jsonl")
