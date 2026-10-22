import unittest
from datetime import datetime, timezone, timedelta
from scripts.collector_health import check


class CollectorHealthTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 22, 20, 0, tzinfo=timezone.utc)

    def row(self, minutes):
        return {"updated_at": (self.now - timedelta(minutes=minutes)).isoformat(),
                "signals": {"5m": {"status": "ok", "grade": "neutral"}}}

    def test_current(self):
        self.assertEqual(check([self.row(60)], self.now)["status"], "current")

    def test_stale(self):
        self.assertEqual(check([self.row(61)], self.now)["status"], "stale")

    def test_missing(self):
        self.assertEqual(check([], self.now)["status"], "missing")

    def test_invalid_future_timestamp_not_accepted(self):
        self.assertEqual(check([self.row(-20)], self.now)["status"], "missing")
