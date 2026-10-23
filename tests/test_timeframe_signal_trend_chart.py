import unittest
from scripts.timeframe_history_dashboard import chart_html, render


class SignalTrendChartTests(unittest.TestCase):
    def test_not_enough_points(self):
        self.assertIn("minimaal twee", chart_html([]))

    def test_chart_and_missing_grade(self):
        rows = [
            {"updated_at": "2026-10-22T10:00:00+00:00",
             "signals": {"5m": {"status": "ok", "grade": "bearish"}}},
            {"updated_at": "2026-10-22T12:00:00+00:00",
             "signals": {"5m": {"status": "ok", "grade": "bullish"}}},
        ]
        page = render(rows)
        self.assertIn("<svg", page)
        self.assertNotIn("<polyline", page)
        self.assertIn("5M", page)
        self.assertNotIn("undefined", page)
