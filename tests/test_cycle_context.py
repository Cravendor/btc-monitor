from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.cycle_context import build, attach, render
from scripts.cycle_history import report, save, DAY, checked
from scripts.cycle_anchor_policy import select
from scripts.market_scenarios import time_ms
from scripts.swing_scenarios import build_swing_scenarios, validate_frozen
from tests.test_price_roadmap import fixture

NOW = '2026-10-24T05:30:00Z'


class CycleContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.history = Path(self.tmp.name) / 'history.json'
        self.config_path = Path(self.tmp.name) / 'config.json'
        self.start = time_ms('2025-01-01T00:00:00Z')
        self.boundary = time_ms(NOW)//DAY*DAY
        self.rows = {t: dict(open_time_ms=t, open=100, high=110, low=90, close=100,
                             base_volume_btc=10, quote_volume_usdt=1000)
                     for t in range(self.start, self.boundary, DAY)}
        self.rows[self.start]['high'] = 200
        self.rows[self.start+30*DAY]['high'] = 300
        self.rows[self.start+40*DAY]['low'] = 50
        self.config = dict(schema_version=1, status='draft', cycle_id='current', previous_cycle_id='prior',
                           previous_cycle_peak_at='2025-01-01T00:00:00Z',
                           previous_peak_window_from='2025-01-01T00:00:00Z',
                           previous_peak_window_through='2025-01-20T00:00:00Z',
                           phase='post_peak', reference_basis='Reviewed historical reference window.',
                           classification_basis='Explicit operational post-peak hypothesis, not a confirmed cycle end.')
        self.write()

    def write(self):
        save(self.history, report({t: checked(c, self.boundary) for t,c in self.rows.items()}, [], self.start, self.boundary, NOW, 'fixture'))
        self.config_path.write_text(json.dumps(self.config))

    def test_draft_produces_review_without_altering_routes_or_original_source(self):
        before = self.history.read_bytes()
        review, context = build(self.history, self.config_path, NOW)
        self.assertEqual(review['status'], 'ready')
        self.assertIsNone(context)
        self.assertEqual((review['anchors']['high'], review['anchors']['low']), (300, 50))
        self.assertNotIn('evidence', review['anchors'])
        self.assertEqual(review['provenance']['validation'], 'local_archive_only')
        feed, now = fixture()
        baseline = build_swing_scenarios(feed, now)
        attach(feed['measurements'][0], self.history, self.config_path)
        self.assertEqual(build_swing_scenarios(feed, now), baseline)
        self.assertEqual(self.history.read_bytes(), before)
        self.assertIn('nog niet geactiveerd', render(feed))

    def test_active_context_survives_freeze_for_both_horizons(self):
        self.config['status'] = 'active'; self.write()
        review, context = build(self.history, self.config_path, NOW)
        self.assertEqual(review['status'], 'ready')
        self.assertEqual(context['source']['observation_kind'], 'local_archive_validation')
        self.assertTrue(select(context, NOW)['status'] == 'calculated')
        feed, now = fixture()
        attach(feed['measurements'][0], self.history, self.config_path)
        routes = build_swing_scenarios(feed, now)['horizons']
        a, b = [r['route_anchors'] for r in routes.values()]
        self.assertEqual(a, b)
        self.assertEqual(a['low'], 50)
        for route in routes.values():
            self.assertTrue(validate_frozen(route))

    def test_active_missing_latest_closed_day_never_falls_back(self):
        self.config['status'] = 'active'; self.write()
        tomorrow = '2026-10-25T05:30:00Z'
        review, context = build(self.history, self.config_path, tomorrow)
        self.assertEqual(review['status'], 'unavailable')
        self.assertEqual(review['missing_days'], 1)
        self.assertEqual(select(context, tomorrow)['status'], 'unavailable')
        feed, now = fixture()
        record = feed['measurements'][0]
        self.rows.pop(self.start+10*DAY); self.write()
        attach(record, self.history, self.config_path)
        for route in build_swing_scenarios(feed, now)['horizons'].values():
            self.assertEqual(route['two_route_assessment']['status'], 'unavailable')
            self.assertTrue(validate_frozen(route))

    def test_reference_window_must_be_complete_and_peak_must_match(self):
        original = deepcopy(self.rows)
        for fault in ('gap', 'higher_peak', 'wrong_date', 'no_reference_basis', 'same_cycle', 'bad_phase'):
            with self.subTest(fault=fault):
                self.rows = deepcopy(original)
                old_config = deepcopy(self.config)
                if fault == 'gap': self.rows.pop(self.start+DAY)
                if fault == 'higher_peak': self.rows[self.start+DAY]['high'] = 220
                if fault == 'wrong_date': self.config['previous_cycle_peak_at'] = '2025-01-02T00:00:00Z'
                if fault == 'no_reference_basis': self.config['reference_basis'] = ''
                if fault == 'same_cycle': self.config['previous_cycle_id'] = 'current'
                if fault == 'bad_phase': self.config['phase'] = 'automatically_bear'
                self.write()
                review, context = build(self.history, self.config_path, NOW)
                self.assertEqual(review['status'], 'unavailable')
                self.assertIsNone(context)
                self.config = old_config

    def test_active_wrong_market_tampering_missing_archive_or_config_field_fail_closed(self):
        self.config['status'] = 'active'; self.write()
        original = self.history.read_bytes()
        for fault in ('market', 'checksum', 'missing_archive', 'missing_phase'):
            with self.subTest(fault=fault):
                self.history.write_bytes(original)
                if fault == 'missing_archive': self.history.unlink()
                elif fault == 'missing_phase':
                    del self.config['phase']; self.config_path.write_text(json.dumps(self.config))
                else:
                    data = json.loads(original)
                    if fault == 'market': data['market'] = 'SPOT'
                    if fault == 'checksum': data['candles'][0]['high'] = 999
                    self.history.write_text(json.dumps(data))
                review, context = build(self.history, self.config_path, NOW)
                self.assertEqual(review['status'], 'unavailable')
                self.assertIsNotNone(context)
                self.assertEqual(select(context, NOW)['status'], 'unavailable')

    def test_config_and_source_hashes_change_independently_anchor_version_stays_stable(self):
        first, unused = build(self.history, self.config_path, NOW)
        self.config['classification_basis'] += ' Review clarified.'; self.write()
        second, unused = build(self.history, self.config_path, NOW)
        self.assertNotEqual(first['provenance']['config_sha256'], second['provenance']['config_sha256'])
        self.assertEqual(first['anchors']['anchor_version_id'], second['anchors']['anchor_version_id'])
        self.rows[self.boundary-DAY]['low'] = 40; self.write()
        third, unused = build(self.history, self.config_path, NOW)
        self.assertNotEqual(second['provenance']['archive_content_sha256'], third['provenance']['archive_content_sha256'])
        self.assertNotEqual(second['anchors']['anchor_version_id'], third['anchors']['anchor_version_id'])
        self.assertEqual(first['anchors']['low'], 50)

    def test_disabled_configuration_and_html_escaping(self):
        self.config['status'] = 'disabled'; self.write()
        self.history.unlink()
        review, context = build(self.history, self.config_path, NOW)
        self.assertEqual(review['status'], 'inactive')
        self.assertIsNone(context)
        review['reason'] = '<script>example</script>'
        html = render({'measurements': [dict(cycle_anchor_review=review)]})
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_unreadable_missing_or_unknown_configuration_cannot_revert_active_policy(self):
        for raw in ('{broken', '[]', '{"schema_version": 1, "status": "typo"}', None):
            if raw is None:
                self.config_path.unlink()
            else:
                self.config_path.write_text(raw)
            review, context = build(self.history, self.config_path, NOW)
            self.assertEqual(review['status'], 'unavailable')
            self.assertIsNotNone(context)
            self.assertEqual(select(context, NOW)['status'], 'unavailable')
