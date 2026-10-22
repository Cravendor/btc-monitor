import unittest
from scripts.context_trend_dashboard import render


class TrendDashboardTests(unittest.TestCase):
    def test_empty_history(self):
        result = render([], "2026-10-22T12:00:00Z")
        self.assertIn("ONTBREEKT", result)
        self.assertIn("24 uur", result)
        self.assertIn("30 dagen", result)

    def test_escapes_unexpected_label(self):
        rows = [{"quality": "provisional_price_only",
                 "source": "Bitget USDT-FUTURES BTCUSDT latest.json",
                 "grade": "neutral", "model_version": "v0.1",
                 "observed_at": "2026-10-22T12:00:00Z"}]
        result = render(rows, "2026-10-22T12:00:00Z")
        self.assertIn("neutral", result)


if __name__ == "__main__":
    unittest.main()
