import unittest
from scripts.signal_performance_report import summarize, render_html


class ReportTests(unittest.TestCase):
    def test_missing_not_counted_as_correct(self):
        rows = [
            {"timeframe": "4h", "grade": "slightly_bullish",
             "outcome": {"status": "evaluated", "verdict": "correct"}},
            {"timeframe": "4h", "grade": "slightly_bullish",
             "outcome": {"status": "unavailable"}},
        ]
        s = summarize(rows)[0]
        self.assertEqual(s["hit_rate"], 100)
        self.assertEqual(s["unavailable"], 1)
        self.assertEqual(s["total"], 2)

    def test_empty_report(self):
        self.assertIn("BTC Signal Performance", render_html([]))

    def test_invalid_grade(self):
        with self.assertRaises(ValueError):
            summarize([{"timeframe": "4h", "grade": "unknown"}])


if __name__ == "__main__":
    unittest.main()
