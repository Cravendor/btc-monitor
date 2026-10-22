import unittest
from datetime import datetime, timezone, timedelta
from scripts.multi_timeframe_signals import assess
from scripts.multi_timeframe_dashboard import render


class EvidenceDiagnosticsTests(unittest.TestCase):
    def test_dashboard_shows_conflict(self):
        feed = {"measurements": [{"metrics": {"multi_timeframe": {"data": {
            "5m": {"status": "ok", "signal": {"status": "provisional", "grade": "neutral",
                  "evidence": {"state": "conflicting"}, "observed_at": "2026-10-22T20:00:00Z"}}
        }}}}]}
        self.assertIn("Trend en momentum tegengesteld", render(feed))

    def test_no_direction_on_flat_candles(self):
        end = datetime(2026, 10, 22, 20, 0, tzinfo=timezone.utc)
        period = 300000
        end_ms = int(end.timestamp() * 1000)
        candles = [{"open_time_ms": end_ms - (24 - i) * period,
                    "open": 100, "high": 101, "low": 99, "close": 100,
                    "base_volume_btc": 10} for i in range(24)]
        result = assess(candles, "5m", end.isoformat())
        self.assertEqual(result["grade"], "neutral")
        self.assertEqual(result["evidence"]["state"], "no_direction")
