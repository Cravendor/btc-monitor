import unittest
from datetime import datetime, timezone
from scripts.bitget_4h_assessment import assess_latest_4h

STEP = 14400000
START = 1792008000000


def example_feed():
    candles = []
    for i in range(24):
        price = 100 + i * 0.5
        candles.append({"open_time_ms": START + STEP*i, "open": price,
                        "high": price+1, "low": price-1, "close": price,
                        "base_volume_btc": 10})
    end = START + 24*STEP
    timestamp = datetime.fromtimestamp(end/1000, timezone.utc).isoformat()
    return {
        "exchange": "bitget", "market": "USDT-FUTURES", "symbol": "BTCUSDT",
        "measurements": [{"status": "ok", "finished_at": timestamp,
                          "metrics": {"candles_4h": {"status": "ok",
                                                    "data": {"candles": candles}}}}]
    }, timestamp


class AssessmentTests(unittest.TestCase):
    def test_provisional_not_final(self):
        feed, now = example_feed()
        result = assess_latest_4h(feed, now)
        self.assertEqual(result["status"], "provisional")
        self.assertEqual(result["data_quality"], "provisional_price_only")

    def test_missing_candles(self):
        feed, now = example_feed()
        feed["measurements"][0]["metrics"]["candles_4h"]["status"] = "error"
        self.assertIsNone(assess_latest_4h(feed, now)["grade"])

    def test_stale(self):
        feed, now = example_feed()
        future = datetime.fromtimestamp(
            datetime.fromisoformat(now).timestamp() + 6*3600,
            timezone.utc).isoformat()
        self.assertEqual(assess_latest_4h(feed, future)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
