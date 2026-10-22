import unittest
from datetime import datetime, timezone, timedelta
from scripts.timeframe_history_dashboard import summarize, render


class TimeframeStatisticsTests(unittest.TestCase):
    def sample(self, hours_ago, grade="neutral"):
        now = datetime(2026, 10, 22, 18, tzinfo=timezone.utc)
        return {"updated_at": (now - timedelta(hours=hours_ago)).isoformat(),
                "signals": {"5m": {"status": "ok", "grade": grade}}}

    def test_insufficient_history_explicit(self):
        records = [self.sample(0), self.sample(1)]
        self.assertIsNone(summarize(records, 24))
        self.assertIn("onvoldoende historische dekking", render(records))

    def test_observations_and_changes(self):
        records = [self.sample(24, "neutral"), self.sample(12, "slightly_bullish"),
                   self.sample(0, "slightly_bearish")]
        stats = summarize(records, 24)
        self.assertEqual(stats["5m"]["observations"], 3)
        self.assertEqual(stats["5m"]["changes"], 2)
        self.assertEqual(stats["5m"]["bullish"], 1)
        self.assertEqual(stats["5m"]["bearish"], 1)
        self.assertEqual(stats["1h"]["observations"], 0)
