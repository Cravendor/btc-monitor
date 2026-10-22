import unittest
from scripts.multi_timeframe_dashboard import render


class MultiTimeframeDashboardTests(unittest.TestCase):
    def test_missing_is_not_neutral(self):
        page = render({"measurements": [{"metrics": {}}]})
        self.assertEqual(page.count("ONTBREEKT"), 14)
        self.assertNotIn("<td>Neutraal</td>", page)

    def test_valid_signal(self):
        feed = {"measurements": [{"metrics": {"multi_timeframe": {
            "data": {"5m": {"status": "ok", "signal": {
                "status": "provisional", "grade": "slightly_bullish",
                "observed_at": "2026-10-22T12:00:00+00:00"}}}}}}]}
        page = render(feed)
        self.assertIn("Licht bullish", page)
        self.assertEqual(page.count("ONTBREEKT"), 13)


if __name__ == "__main__":
    unittest.main()
