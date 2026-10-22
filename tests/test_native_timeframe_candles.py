import unittest
from datetime import datetime, timezone
from scripts.native_timeframe_candles import validate_rows, PERIOD_MS


class NativeTimeframeCandlesTests(unittest.TestCase):
    def test_all_supported_intervals(self):
        for tf, p in PERIOD_MS.items():
            with self.subTest(tf=tf):
                offset = 4*86400000 if tf == "1w" else 0
                rows = [[str(offset+p*i), "100", "102", "98", "101", "10", "1000"]
                        for i in range(100, 124)]
                now = datetime.fromtimestamp((offset+p*124)/1000, timezone.utc).isoformat()
                result = validate_rows(rows, tf, now)
                self.assertEqual(len(result["candles"]), 24)
                self.assertTrue(result["closed_only"])

    def test_missing_recent_candle(self):
        p = PERIOD_MS["5m"]
        rows = [[str(p*i), "100", "102", "98", "101", "10", "1000"]
                for i in range(100, 123)]
        now = datetime.fromtimestamp(p*124/1000, timezone.utc).isoformat()
        with self.assertRaises(ValueError):
            validate_rows(rows, "5m", now)

    def test_rejects_conflicting_duplicates(self):
        p = PERIOD_MS["1h"]
        rows = [[str(p*i), "100", "102", "98", "101", "10", "1000"]
                for i in range(100, 124)]
        rows.append([str(p*123), "100", "102", "98", "99", "10", "1000"])
        now = datetime.fromtimestamp(p*124/1000, timezone.utc).isoformat()
        with self.assertRaisesRegex(ValueError, "conflicting"):
            validate_rows(rows, "1h", now)


if __name__ == "__main__":
    unittest.main()
