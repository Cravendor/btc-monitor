import unittest
from scripts.market_intelligence import Indicator, aggregate


def item(name, score, quality="verified", weight=1):
    return Indicator(name, "4h", score, quality, weight,
                     "2026-10-22T12:00:00+00:00", "Bitget", "Test observation")


class ScoringTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(aggregate([])["label"], "unavailable")

    def test_missing_not_neutral(self):
        result = aggregate([item("price", 2), item("cvd", None, "missing")])
        self.assertEqual(result["label"], "unavailable")
        self.assertEqual(result["coverage"], 0.5)

    def test_bullish(self):
        result = aggregate([item("price", 2), item("volume", 1)])
        self.assertEqual(result["label"], "strong_bull")

    def test_unverified_excluded(self):
        result = aggregate([item("price", -2), item("cvd", 2, "unverified")])
        self.assertEqual(result["label"], "unavailable")

    def test_missing_score_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([item("cvd", 0, "missing")])


if __name__ == "__main__":
    unittest.main()
