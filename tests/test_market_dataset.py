import unittest
from scripts.market_dataset import build_history


class MarketDatasetTests(unittest.TestCase):
    def test_no_future_macro_leakage(self):
        signal = {"id": "a", "issued_at": "2026-10-22T12:00:00Z",
                  "market": "bitget_btcusdt", "timeframe": "4h",
                  "grade": "slightly_bullish", "model_version": "v1"}
        events = [
            {"retrieved_at": "2026-10-22T11:00:00Z",
             "source_url": "https://www.federalreserve.gov",
             "status": "parsed_unconfirmed", "events": []},
            {"retrieved_at": "2026-10-22T13:00:00Z",
             "source_url": "https://www.federalreserve.gov",
             "status": "parsed_unconfirmed", "events": []},
        ]
        rows = build_history([signal], events, [])
        self.assertEqual(len(rows[0]["macro_as_known_at_issue"]), 1)
        self.assertEqual(rows[0]["outcome"]["status"], "unavailable")

    def test_duplicate_signal_rejected(self):
        s = {"id": "a", "issued_at": "2026-10-22T12:00:00Z",
             "market": "bitget_btcusdt", "timeframe": "4h",
             "grade": "neutral", "model_version": "v1"}
        with self.assertRaises(ValueError):
            build_history([s, s], [], [])


if __name__ == "__main__":
    unittest.main()
