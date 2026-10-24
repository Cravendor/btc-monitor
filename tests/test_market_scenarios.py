from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import unittest

from scripts.home_dashboard import render
from scripts.market_scenarios import STEP, build_scenarios, iso


def fixture():
    boundary = 1000 * STEP
    rows = [{'open_time_ms': boundary - (21-i)*STEP, 'open': 100.0,
             'high': 110.0, 'low': 90.0, 'close': 100.0, 'base_volume_btc': 10.0}
            for i in range(21)]
    now = iso(boundary + 5 * 60000)
    feed = {'measurements': [{'exchange': 'bitget', 'market': 'USDT-FUTURES',
                             'symbol': 'BTCUSDT', 'collection_source': 'nas',
                             'started_at': now, 'finished_at': now, 'status': 'ok',
                             'metrics': {'candles_4h': {'status': 'ok', 'observed_at': now,
                                         'data': {'candles': rows, 'interval': '4H', 'closed_only': True}},
                                         'futures_price': {'status': 'ok', 'data': {
                                             'lastPr': '101', 'ts': str(boundary + 300000)}}}}]}
    return feed, now


class MarketScenarioTests(unittest.TestCase):
    def test_exact_range_atr_projection_and_volume_without_lookahead(self):
        feed, now = fixture()
        last = feed['measurements'][0]['metrics']['candles_4h']['data']['candles'][-1]
        last.update(high=150, close=140, base_volume_btc=20)
        result = build_scenarios(feed, now)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual((result['support'], result['resistance'], result['atr14']), (90, 110, 20))
        up = result['scenarios'][0]
        self.assertEqual((up['trigger'], up['invalidation'], up['targets']), (112, 108, [132, 152]))
        self.assertEqual(result['scenarios'][2]['targets'], [68, 48])
        self.assertEqual(result['state'], 'bullish_breakout')
        self.assertEqual(result['volume_ratio'], 2)
        self.assertAlmostEqual(result['volume_24h_ratio'], 70/60)
        self.assertNotIn('probability', result)

    def test_downside_and_touch_are_not_confused_with_a_close_break(self):
        feed, now = fixture()
        last = feed['measurements'][0]['metrics']['candles_4h']['data']['candles'][-1]
        last.update(low=80, high=130, close=100)
        self.assertEqual(build_scenarios(feed, now)['state'], 'range')
        last.update(close=87)
        self.assertEqual(build_scenarios(feed, now)['state'], 'bearish_breakdown')
        last.update(close=88)
        self.assertEqual(build_scenarios(feed, now)['state'], 'range')

    def test_bad_or_missing_latest_never_reuses_older_green_snapshot(self):
        feed, now = fixture()
        for change in ('gap', 'duplicate', 'short', 'bad_price', 'wrong_market', 'stale', 'source_error', 'latest_missing'):
            with self.subTest(change=change):
                sample = deepcopy(feed)
                sample['measurements'].append(deepcopy(feed['measurements'][0]))
                m = sample['measurements'][0]
                rows = m['metrics']['candles_4h']['data']['candles']
                if change == 'gap': rows.pop(10)
                if change == 'duplicate': rows.insert(3, deepcopy(rows[3]))
                if change == 'short': del rows[:3]
                if change == 'bad_price': rows[-1]['close'] = float('nan')
                if change == 'wrong_market': m['market'] = 'SPOT'
                if change == 'stale': m['started_at'] = iso(1000 * STEP - 2 * 3600000)
                if change == 'source_error': m['metrics']['candles_4h']['status'] = 'error'
                if change == 'latest_missing': rows.pop()
                result = build_scenarios(sample, now)
                self.assertEqual(result['status'], 'unavailable')
                self.assertEqual(result['scenarios'], [])

    def test_open_candle_cannot_activate_and_next_boundary_requires_new_data(self):
        feed, now = fixture()
        feed['measurements'][0]['metrics']['candles_4h']['data']['candles'].append(
            {'open_time_ms': 1000*STEP, 'open': 100, 'high': 900, 'low': 90, 'close': 800, 'base_volume_btc': 999})
        result = build_scenarios(feed, now)
        self.assertEqual(result['state'], 'range')
        self.assertEqual(result['resistance'], 110)
        new_time = iso(1001*STEP + 300000)
        m = feed['measurements'][0]
        m['started_at'] = m['finished_at'] = m['metrics']['candles_4h']['observed_at'] = new_time
        m['metrics']['candles_4h']['data']['candles'].pop()
        self.assertEqual(build_scenarios(feed, new_time)['status'], 'unavailable')

    def test_zero_baseline_and_invalid_time_have_no_invented_ratio_or_levels(self):
        feed, now = fixture()
        for row in feed['measurements'][0]['metrics']['candles_4h']['data']['candles']:
            row['base_volume_btc'] = 0
        r = build_scenarios(feed, now)
        self.assertIsNone(r['volume_ratio'])
        self.assertIsNone(r['volume_24h_ratio'])
        self.assertEqual(build_scenarios(feed, 'no-time')['status'], 'unavailable')

    def test_provider_delta_needs_exact_market_window_and_scope(self):
        feed, now = fixture()
        m = feed['measurements'][0]
        proof = {'status': 'ok', 'coverage_verified': True, 'exchange': 'bitget',
                 'symbol': 'BTCUSDT', 'market': 'spot', 'unit': 'BTC',
                 'coverage_scope': 'bitget_public_history_only',
                 'coverage_method': 'bitget_history_exhaustion_and_exact_volume_v1',
                 'interval_start_ms': 999*STEP, 'interval_end_ms': 1000*STEP,
                 'validated_delta_btc': '-3.5'}
        m['cvd_4h'] = {'markets': {'spot': proof}}
        self.assertEqual(build_scenarios(feed, now)['provider_deltas'], {'spot': -3.5})
        for key, value in (('interval_start_ms', 998*STEP), ('market', 'usdt_futures'),
                           ('coverage_verified', False), ('validated_delta_btc', 'NaN')):
            original = proof[key]
            proof[key] = value
            self.assertEqual(build_scenarios(feed, now)['provider_deltas'], {})
            proof[key] = original

    def test_home_links_methods_and_staleness_guard_are_present_without_fake_levels(self):
        feed, now = fixture()
        page = render(feed, now)
        for href in ('btc-dashboard.html', 'btc-timeframes.html', 'btc-signal-history.html'):
            self.assertIn('href="' + href + '"', page)
        for text in ('0,1 × ATR14', 'Ontkracht bij', 'geen Wilder-ATR', 'geen slagingspercentages',
                     'geen Wall Street-psychologiefase', 'levels.hidden=true', 'Date.now()>=expiry'):
            self.assertIn(text, page)
        missing = render({}, now)
        self.assertIn('ONVOLDOENDE DATA', missing)
        self.assertNotIn('id="action-levels"', missing)
        self.assertNotIn('112,0 USDT', missing)

    def test_pages_pipeline_publishes_home_and_preserves_measurement_view(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root/'.github/workflows/pages.yml').read_text()
        self.assertIn('cp index.html _site/btc-dashboard.html', workflow)
        self.assertIn('python -m scripts.home_dashboard data/latest.json _site/index.html', workflow)
        self.assertIn('- scripts/market_scenarios.py', workflow)
        self.assertIn('href="index.html"', (root/'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
