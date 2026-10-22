import unittest
from scripts.derivatives_context import derivatives_context

NOW = {"market": "bitget_USDT-FUTURES_BTCUSDT",
       "observed_at": "2026-10-22T12:00:00Z",
       "funding_rate": 0.0001, "open_interest": 110}
PREV = {"market": "bitget_USDT-FUTURES_BTCUSDT",
        "observed_at": "2026-10-22T08:00:00Z",
        "open_interest": 100}


class DerivativesTests(unittest.TestCase):
    def test_context_without_direction(self):
        result = derivatives_context(NOW, PREV)
        self.assertEqual(result["oi_change_pct"], 10)
        self.assertIsNone(result["directional_grade"])

    def test_missing_previous(self):
        result = derivatives_context(NOW)
        self.assertIsNone(result["oi_change_pct"])

    def test_other_market(self):
        result = derivatives_context(NOW, dict(PREV, market="spot"))
        self.assertIsNone(result["oi_change_pct"])


if __name__ == "__main__":
    unittest.main()
