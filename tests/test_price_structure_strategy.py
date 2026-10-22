import unittest
from datetime import datetime, timezone
from scripts.price_structure_strategy import score_closed_4h

STEP = 14400000
START = 1792008000000

def candles(up=True):
    out = []
    for i in range(24):
        close = 100 + (i * 0.5 if up else -i * 0.5)
        out.append({"open_time_ms": START + i * STEP,
                    "open": close, "high": close + 1, "low": close - 1,
                    "close": close, "base_volume_btc": 10})
    return out

class PriceStrategyTests(unittest.TestCase):
    def test_provisional_only(self):
        series = candles()
        end = series[-1]["open_time_ms"] + STEP
        now = datetime.fromtimestamp(end / 1000, timezone.utc).isoformat()
        r = score_closed_4h(series, now)
        self.assertEqual(r["status"], "provisional")
        self.assertIsNone(r["volume_directional_score"])
        self.assertEqual(r["confidence"], "low")

    def test_gaps_rejected(self):
        series = candles()
        series.pop(4)
        end = series[-1]["open_time_ms"] + STEP
        now = datetime.fromtimestamp(end / 1000, timezone.utc).isoformat()
        self.assertEqual(score_closed_4h(series, now)["status"], "unavailable")

    def test_incomplete_candle_excluded(self):
        series = candles()[:23]
        end = series[-1]["open_time_ms"] + STEP
        now = datetime.fromtimestamp(end / 1000, timezone.utc).isoformat()
        self.assertEqual(score_closed_4h(series, now)["status"], "unavailable")

if __name__ == "__main__":
    unittest.main()
