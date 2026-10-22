import unittest
from scripts.signal_validation import summarize_predictions


def pair(identifier, direction, end_price, observed="2026-10-23T12:00:00Z"):
    return {"prediction": {
        "id": identifier, "issued_at": "2026-10-22T12:00:00Z",
        "horizon_hours": 24, "market": "bitget_btcusdt",
        "entry_price": 100, "direction": direction, "model_version": "v1"
    }, "outcome": {"observed_at": observed,
                    "market": "bitget_btcusdt", "price": end_price}}


class SignalValidationTests(unittest.TestCase):
    def test_counts_and_missing_not_zero(self):
        data = [pair("a", "bull", 110), pair("b", "bear", 110),
                pair("c", "bull", 100),
                pair("d", "bear", 90, "2026-10-24T12:00:00Z")]
        report = summarize_predictions(data)[0]
        self.assertEqual(report["correct"], 1)
        self.assertEqual(report["incorrect"], 1)
        self.assertEqual(report["flat"], 1)
        self.assertEqual(report["unavailable"], 1)
        self.assertEqual(report["hit_rate"], 0.5)
        self.assertEqual(report["directional_sample"], 2)

    def test_no_outcomes(self):
        self.assertEqual(summarize_predictions([]), [])


if __name__ == "__main__":
    unittest.main()
