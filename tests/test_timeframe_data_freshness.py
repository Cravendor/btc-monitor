import unittest
from scripts.timeframe_history_dashboard import freshness_html, render


class FreshnessTests(unittest.TestCase):
    def test_no_valid_measurements(self):
        self.assertIn("ONTBREEKT", freshness_html([]))

    def test_valid_timestamp_and_missing_timeframe(self):
        records = [{"updated_at": "2026-10-22T20:00:00+00:00",
                    "signals": {"5m": {"status": "ok", "grade": "neutral"}}}]
        page = render(records)
        self.assertIn('data-updated="2026-10-22T20:00:00+00:00"', page)
        self.assertIn("5M: beschikbaar", page)
        self.assertIn("1H: ONTBREEKT", page)
        self.assertIn("Date.now()", page)

    def test_rejects_invalid_timestamp(self):
        self.assertIn("ONTBREEKT", freshness_html([{"updated_at": "invalid", "signals": {}}]))
