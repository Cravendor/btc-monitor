import unittest
from datetime import datetime, timezone
from scripts.multi_timeframe_signals import assess, INTERVAL_MS


class MultiTimeframeTests(unittest.TestCase):
    def candles(self, tf, last=102):
        period = INTERVAL_MS[tf]
        start = 100 * period + (4 * 86400000 if tf == "1w" else 0)
        return [{"open_time_ms": start + i * period,
                 "open": 100, "high": 110, "low": 90,
                 "close": last if i == 23 else 100,
                 "base_volume_btc": 10} for i in range(24)]

    def test_supported_timeframes(self):
        for tf, period in INTERVAL_MS.items():
            with self.subTest(tf=tf):
                now = datetime.fromtimestamp((124 * period + (4 * 86400000 if tf == "1w" else 0)) / 1000, timezone.utc).isoformat()
                result = assess(self.candles(tf), tf, now)
                self.assertEqual(result["status"], "provisional")
                self.assertEqual(result["confidence"], "low")

    def test_missing_candle_unavailable(self):
        period = INTERVAL_MS["15m"]
        now = datetime.fromtimestamp(124 * period / 1000, timezone.utc).isoformat()
        self.assertEqual(assess(self.candles("15m")[:-1], "15m", now)["status"], "unavailable")

    def test_duplicate_candle_unavailable(self):
        period = INTERVAL_MS["4h"]
        now = datetime.fromtimestamp(124 * period / 1000, timezone.utc).isoformat()
        candles = self.candles("4h")
        candles[-1]["open_time_ms"] = candles[-2]["open_time_ms"]
        self.assertEqual(assess(candles, "4h", now)["status"], "unavailable")

    def test_stale_unavailable(self):
        period = INTERVAL_MS["1h"]
        now = datetime.fromtimestamp(127 * period / 1000, timezone.utc).isoformat()
        self.assertEqual(assess(self.candles("1h"), "1h", now)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
