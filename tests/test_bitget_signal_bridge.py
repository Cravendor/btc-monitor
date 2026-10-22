import unittest
from scripts.bitget_signal_bridge import read_latest


def feed():
    return {"exchange": "bitget", "market": "USDT-FUTURES", "symbol": "BTCUSDT",
            "measurements": [{"status": "ok", "finished_at": "2026-10-22T12:00:00Z",
                              "metrics": {"futures_price": {"status": "ok",
                                  "observed_at": "2026-10-22T12:00:00Z",
                                  "url": "https://api.bitget.com/test",
                                  "data": {"lastPr": "82000"}}}}]}


class BridgeTests(unittest.TestCase):
    def test_read_only_no_grade(self):
        result = read_latest(feed(), "2026-10-22T12:01:00Z")
        self.assertEqual(result["status"], "observed_unscored")
        self.assertIsNone(result["grade"])
        self.assertEqual(result["observations"][0]["value"], 82000)

    def test_stale_excluded(self):
        result = read_latest(feed(), "2026-10-22T18:00:00Z")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["observations"], [])

    def test_wrong_market_rejected(self):
        bad = feed()
        bad["market"] = "SPOT"
        with self.assertRaises(ValueError):
            read_latest(bad, "2026-10-22T12:01:00Z")


if __name__ == "__main__":
    unittest.main()
