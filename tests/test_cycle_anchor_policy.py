from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import unittest
from scripts.cycle_anchor_policy import select,validate,DAY
from scripts.market_scenarios import time_ms
from scripts.swing_scenarios import build_swing_scenarios,validate_frozen
from scripts.two_routes import render_meter
from tests.test_price_roadmap import fixture


def context(now='2026-10-24T05:30:00Z'):
    start=time_ms('2025-01-01T00:00:00Z');end=time_ms(now)//DAY*DAY
    rows=[dict(open_time_ms=t,open=100,high=110,low=90,close=100) for t in range(start,end,DAY)]
    rows[0]['high']=200  # Previous completed cycle peak.
    rows[10]['low']=50  # Inter-peak bottom.
    rows[30]['high']=300  # Latest cycle peak.
    rows[365+5]['low']=30  # Lowest low since latest peak.
    return dict(schema_version=1,status='active',cycle_id='test-cycle-2',previous_cycle_id='test-cycle-1',
        classification_basis='Explicit fixture classification, no phase inference.',previous_cycle_peak_at='2025-01-01T00:00:00Z',phase='post_peak',
        source=dict(status='ok',exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',interval='1d',
            closed_only=True,observed_at=now,candles=rows))


class CycleAnchorPolicyTests(unittest.TestCase):
    def test_uses_peak_interval_not_recent_range_or_calendar_year(self):
        r=select(context(),'2026-10-24T05:30:00Z')
        self.assertEqual(r['status'],'calculated')
        self.assertEqual((r['high'],r['low']),(300,30))
        self.assertTrue(validate(r))
        self.assertFalse(r['bottom_confirmed'])

    def test_missing_history_duplicate_open_or_wrong_market_never_becomes_neutral(self):
        for fault in ('gap','duplicate','open','market','stale','future_peak','inactive','same_cycle','no_basis'):
            c=context()
            if fault=='gap':c['source']['candles'].pop(3)
            if fault=='duplicate':c['source']['candles'].append(c['source']['candles'][0])
            if fault=='open':c['source']['candles'].append(dict(open_time_ms=time_ms('2026-10-24T00:00:00Z'),open=1,high=2,low=1,close=1))
            if fault=='market':c['source']['market']='SPOT'
            if fault=='stale':c['source']['observed_at']='2026-10-22T05:30:00Z'
            if fault=='future_peak':c['previous_cycle_peak_at']='2027-01-01T00:00:00Z'
            if fault=='inactive':c['status']='draft'
            if fault=='same_cycle':c['previous_cycle_id']=c['cycle_id']
            if fault=='no_basis':c['classification_basis']=''
            self.assertEqual(select(c,'2026-10-24T05:30:00Z')['status'],'unavailable',fault)

    def test_calendar_rollover_does_not_reset_peak_or_running_low(self):
        now='2027-01-02T05:30:00Z';c=context(now);r=select(c,now)
        self.assertEqual(r['status'],'calculated')
        self.assertEqual((r['high'],r['low']),(300,30))
        self.assertEqual(r['cycle_id'],c['cycle_id'])

    def test_advance_uses_low_between_peaks_post_peak_uses_new_window(self):
        c=context();c['phase']='advance'
        before=select(c,'2026-10-24T05:30:00Z')
        self.assertEqual(before['low'],50)
        c['phase']='post_peak'
        after=select(c,'2026-10-24T05:30:00Z')
        self.assertEqual(after['low'],30)
        self.assertNotEqual(before['anchor_version_id'],after['anchor_version_id'])

    def test_higher_or_equal_low_does_not_move_anchor(self):
        c=context();first=select(c,'2026-10-24T05:30:00Z')
        for low in (40,30):
            c['source']['candles'][-1]['low']=low
            after=select(c,'2026-10-24T05:30:00Z')
            self.assertEqual(after['low_at'],first['low_at'])
            self.assertEqual(after['anchor_version_id'],first['anchor_version_id'])

    def test_strictly_higher_peak_restarts_low_window_equal_high_does_not(self):
        c=context();first=select(c,'2026-10-24T05:30:00Z')
        c['source']['candles'][-2]['high']=300
        equal=select(c,'2026-10-24T05:30:00Z')
        self.assertEqual(equal['anchor_version_id'],first['anchor_version_id'])
        c['source']['candles'][-2]['high']=400
        after=select(c,'2026-10-24T05:30:00Z')
        self.assertEqual((after['high'],after['low']),(400,90))
        self.assertNotEqual(after['anchor_version_id'],first['anchor_version_id'])
        c['source']['candles'][-1]['high']=500
        self.assertEqual(select(c,'2026-10-24T05:30:00Z')['status'],'unavailable')

    def test_same_candle_peak_low_is_excluded_and_peak_must_exceed_previous_cycle(self):
        c=context();c['source']['candles'][30]['low']=1
        self.assertEqual(select(c,'2026-10-24T05:30:00Z')['low'],30)
        c['phase']='advance'
        self.assertEqual(select(c,'2026-10-24T05:30:00Z')['low'],50)
        c['source']['candles'][0]['high']=500
        self.assertEqual(select(c,'2026-10-24T05:30:00Z')['status'],'unavailable')

    def test_same_anchor_version_until_extreme_or_policy_changes(self):
        c=context();r=select(c,'2026-10-24T05:30:00Z')
        later=select(c,'2026-10-24T05:40:00Z')
        self.assertEqual(r['anchor_version_id'],later['anchor_version_id'])
        c['source']['candles'][-1]['low']=20
        newer=select(c,'2026-10-24T05:40:00Z')
        self.assertNotEqual(r['anchor_version_id'],newer['anchor_version_id'])
        self.assertEqual(r['low'],30)  # Original record remains unchanged.

    def test_frozen_evidence_detects_changed_anchor_even_after_set_rehash(self):
        feed,now=fixture();feed['measurements'][0]['cycle_anchor_context']=context(now)
        bundle=build_swing_scenarios(feed,now)
        r=bundle['horizons']['swing'];self.assertTrue(validate_frozen(r))
        r['route_anchors']['high']+=1
        r.pop('scenario_set_id');r['scenario_set_id']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        with self.assertRaisesRegex(ValueError,'Cycle anchors'):validate_frozen(r)

    def test_both_horizons_share_macro_anchors_and_missing_context_leaves_current_model(self):
        feed,now=fixture();baseline=build_swing_scenarios(feed,now)
        self.assertTrue(all(r['model_version']=='two_routes_daily_weekly_v4_anchors' for r in baseline['horizons'].values()))
        feed['measurements'][0]['cycle_anchor_context']=context(now)
        bundle=build_swing_scenarios(feed,now)
        a,b=[r['route_anchors'] for r in bundle['horizons'].values()]
        self.assertEqual(a,b)
        for mode,r in bundle['horizons'].items():
            self.assertTrue(validate_frozen(r))
            self.assertEqual(r['two_route_assessment']['anchor_scope'],'cycle_peaks_running_low')
            self.assertIn('Zelfde macroankers',render_meter(r,mode))

    def test_activated_policy_with_incomplete_data_cannot_silently_reuse_range(self):
        feed,now=fixture();c=context(now);c['source']['candles'].pop(0)
        feed['measurements'][0]['cycle_anchor_context']=c
        for mode,r in build_swing_scenarios(feed,now)['horizons'].items():
            self.assertEqual(r['two_route_assessment']['status'],'unavailable')
            self.assertIsNone(r['two_route_assessment']['combined']['score'])
            self.assertNotIn('gauge-needle',render_meter(r,mode))
            self.assertTrue(validate_frozen(r))
