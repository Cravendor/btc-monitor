import unittest
from scripts.timeframe_history_dashboard import collector_health_html, render


class CollectorHealthDashboardTests(unittest.TestCase):
    def test_missing_health(self):
        self.assertIn("ONTBREEKT", collector_health_html(None))

    def test_health_status_and_age_script(self):
        health = {"status": "current", "checked_at": "2026-10-22T20:32:43+00:00",
                  "last_snapshot_at": "2026-10-22T20:32:10+00:00"}
        page = render([], health)
        self.assertIn("collector-watchdog", page)
        self.assertIn("CONTROLE VEROUDERD", page)
        self.assertIn("20:32:10", page)

    def test_rejects_bad_checked_at(self):
        self.assertIn("ONGELDIGE", collector_health_html({"checked_at": "not-a-date"}).upper())
