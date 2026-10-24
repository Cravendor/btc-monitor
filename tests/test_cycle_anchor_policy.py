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
    rows[30]['high']=300  # Cycle high outside 2026 and recent source windows.
    rows[365+5]['low']=30  # Bear-year low outside recent source windows.
    return dict(schema_version=1,status='active',cycle_id='test-cycle-2',previous_cycle_id='test-cycle-1',
        classification_basis='Explicit fixture classification, no phase inference.',cycle_start='2025-01-01T00:00:00Z',bear_year=2026,
        source=dict(status='ok',exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',interval='1d',
            closed_only=True,observed_at=now,candles=rows))


class CycleAnchorPolicyTests(unittest.TestCase):
    def test_uses_whole_bear_year_and_whole_cycle_not_recent_range(self):
        r=select(context(),'2026-10-24T05:30:00Z')
        self.assertEqual(r['status'],'calculated')
        self.assertEqual((r['high'],r['low']),(300,30))
        self.assertTrue(validate(r))
        self.assertFalse(r['bottom_confirmed'])

    def test_missing_history_duplicate_open_or_wrong_market_never_becomes_neutral(self):
        for fault in ('gap','duplicate','open','market','stale','future_year','inactive','same_cycle','no_basis'):
            c=context()
            if fault=='gap':c['source']['candles'].pop(3)
            if fault=='duplicate':c['source']['candles'].append(c['source']['candles'][0])
            if fault=='open':c['source']['candles'].append(dict(open_time_ms=time_ms('2026-10-24T00:00:00Z'),open=1,high=2,low=1,close=1))
            if fault=='market':c['source']['market']='SPOT'
            if fault=='stale':c['source']['observed_at']='2026-10-22T05:30:00Z'
            if fault=='future_year':c['bear_year']=2027
            if fault=='inactive':c['status']='draft'
            if fault=='same_cycle':c['previous_cycle_id']=c['cycle_id']
            if fault=='no_basis':c['classification_basis']=''
            self.assertEqual(select(c,'2026-10-24T05:30:00Z')['status'],'unavailable',fault)

    def test_previous_bear_year_kept_after_calendar_year_rollover(self):
        now='2027-01-02T05:30:00Z';c=context(now);r=select(c,now)
        self.assertEqual(r['status'],'calculated');self.assertEqual(r['bear_year'],2026)
        self.assertEqual(r['cycle_id'],c['cycle_id'])
        self.assertEqual(r['bear_through'],'2027-01-01T00:00:00+00:00')

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
            self.assertEqual(r['two_route_assessment']['anchor_scope'],'explicit_cycle_bear_year')
            self.assertIn('Zelfde macroankers',render_meter(r,mode))

    def test_activated_policy_with_incomplete_data_cannot_silently_reuse_range(self):
        feed,now=fixture();c=context(now);c['source']['candles'].pop(0)
        feed['measurements'][0]['cycle_anchor_context']=c
        for mode,r in build_swing_scenarios(feed,now)['horizons'].items():
            self.assertEqual(r['two_route_assessment']['status'],'unavailable')
            self.assertIsNone(r['two_route_assessment']['combined']['score'])
            self.assertNotIn('gauge-needle',render_meter(r,mode))
            self.assertTrue(validate_frozen(r))
