import unittest
from datetime import datetime, timezone, timedelta
from scripts.collector_health import check
from scripts.multi_timeframe_dashboard import render as render_timeframes
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


class PersistedHealthPublicationTests(unittest.TestCase):
    def test_current_stale_and_missing_reports_remain_renderable(self):
        now = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
        for state, minutes in (("current", 5), ("stale", 90), ("missing", None)):
            with self.subTest(state=state):
                rows = [] if minutes is None else [{
                    "updated_at": (now - timedelta(minutes=minutes)).isoformat(),
                    "signals": {"5m": {"status": "ok", "grade": "neutral"}}}]
                report = check(rows, now)
                self.assertEqual(report["status"], state)
                self.assertEqual(report["schema_version"], 3)
                history = render(rows, report)
                current = render_timeframes({}, report)
                for page in (history, current):
                    self.assertIn("Geschiedenis ontbreekt", page)
                    self.assertNotIn("nieuw tijdvakrapport vereist", page)
                    self.assertIn(now.isoformat(), page)
                self.assertIn('data-status="' + state + '"', history)
