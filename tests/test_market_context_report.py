import unittest
from scripts.market_context_report import combine_context


class ContextTests(unittest.TestCase):
    def test_derivatives_do_not_override_price(self):
        price = {"status": "provisional", "grade": "neutral",
                 "score": 0, "confidence": "low",
                 "price_vs_20_prior_pct": 0.3, "volume_ratio": 2}
        deriv = {"status": "context_only", "funding_rate": 0.001,
                 "open_interest": 200, "oi_change_pct": 30}
        result = combine_context(price, deriv)
        self.assertEqual(result["grade"], "neutral")
        self.assertEqual(result["derivatives_status"], "context_only")
        self.assertEqual(result["hypothesis_a"], "not_evaluated")

    def test_missing_price(self):
        self.assertIsNone(combine_context({"status": "unavailable"})["grade"])


if __name__ == "__main__":
    unittest.main()
