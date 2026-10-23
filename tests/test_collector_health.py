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

    def test_coverage_detects_long_gaps(self):
        report = check([self.row(240), self.row(30), self.row(0)], self.now)
        coverage = report["coverage_24h"]
        self.assertEqual(coverage["expected_snapshots"], 48)
        self.assertEqual(coverage["observed_snapshots"], 3)
        self.assertEqual(coverage["max_observed_gap_seconds"], 12600)
        self.assertEqual(coverage["status"], "gaps_detected")

    def test_coverage_deduplicates_and_excludes_outside_window(self):
        report = check([self.row(0), self.row(0), self.row(30), self.row(1500)], self.now)
        self.assertEqual(report["coverage_24h"]["observed_snapshots"], 2)
        self.assertEqual(report["coverage_24h"]["status"], "gaps_detected")

    def test_invalid_future_timestamp_not_accepted(self):
        self.assertEqual(check([self.row(-20)], self.now)["status"], "missing")
