import unittest
from datetime import datetime, timezone, timedelta
from scripts.history_coverage import coverage, coverage_html
from scripts.timeframe_history_dashboard import summarize, chart_html


class CoverageTests(unittest.TestCase):
    end = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)

    def row(self, minutes, signals=None):
        return {'updated_at': (self.end - timedelta(minutes=minutes)).isoformat(),
                'signals': signals or {}}

    def test_new_archive_is_not_48_failed_runs(self):
        c = coverage([self.row(0)], self.end)
        self.assertEqual((c['observed_intervals'], c['history_unavailable_intervals'],
                          c['missing_measurement_intervals']), (1, 47, 0))

    def test_empty_archive_is_unknown_not_zero_validity(self):
        c = coverage([], self.end)
        self.assertEqual(c['history_unavailable_intervals'], 48)
        self.assertEqual(c['missing_measurement_intervals'], 0)

    def test_boundary_and_internal_gaps_count(self):
        c = coverage([self.row(1500), self.row(120), self.row(60)], self.end)
        self.assertEqual(c['history_unavailable_intervals'], 0)
        self.assertEqual(c['missing_measurement_intervals'], 46)
        self.assertEqual(c['max_window_gap_seconds'], 1320 * 60)

    def test_extra_runs_cannot_mask_missing_intervals(self):
        rows = [self.row(1500)] + [self.row(i / 10) for i in range(100)]
        c = coverage(rows + rows, self.end)
        self.assertEqual(c['observed_snapshots'], 100)
        self.assertEqual(c['observed_intervals'], 1)
        self.assertLessEqual(c['coverage_percent'], 100)
        self.assertEqual(c['missing_measurement_intervals'], 47)

    def test_complete_window_and_exact_boundaries(self):
        c = coverage([self.row(i * 30) for i in range(49)], self.end)
        self.assertEqual(c['observed_intervals'], 48)
        self.assertEqual(c['status'], 'complete')
        self.assertEqual(c['coverage_percent'], 100)

    def test_invalid_and_future_rows_never_start_archive(self):
        c = coverage([self.row(-1), {'updated_at': '2020-01-01', 'signals': {}},
                      {'updated_at': 'invalid', 'signals': {}}, None], self.end)
        self.assertEqual(c['history_unavailable_intervals'], 48)

    def test_failed_signals_count_as_presence_but_not_neutral(self):
        rows = [self.row(0, {'5m': {'status': 'error', 'grade': 'neutral'}})]
        self.assertEqual(coverage(rows, self.end)['observed_intervals'], 1)
        s = summarize(rows + rows, 24)['5m']
        self.assertEqual(s['observations'], 0)
        self.assertEqual(s['neutral'], 0)
        self.assertEqual(s['unavailable'], 1)

    def test_legacy_health_and_invalid_counters_not_reinterpreted(self):
        self.assertIn('ONTBREEKT', coverage_html({'expected_snapshots': 48, 'observed_snapshots': 60}))
        self.assertIn('ONTBREEKT', coverage_html({'expected_snapshots': 48,
            'observed_intervals': 49, 'history_unavailable_intervals': 0,
            'missing_measurement_intervals': 0}))

    def test_chart_connects_only_nearby_valid_points(self):
        signal = {'5m': {'status': 'ok', 'grade': 'bullish'}}
        self.assertIn('<polyline', chart_html([self.row(30, signal), self.row(0, signal)]))
        self.assertNotIn('<polyline', chart_html([self.row(60, signal), self.row(0, signal)]))
