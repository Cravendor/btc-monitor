from copy import deepcopy
import hashlib
import json
import unittest
from scripts.route_anchors import build,validate
from scripts.swing_scenarios import build_swing_scenarios,validate_frozen
from scripts.two_routes import assess,render_meter
from tests.test_price_roadmap import fixture


def rows():
    data=[dict(open_time_ms=i*86400000,high=150-i,low=100-i) for i in range(35)]
    data[3]['high']=220
    data[10]['low']=60
    return data


class RouteAnchorTests(unittest.TestCase):
    def test_full_history_top_and_later_low_not_recent_twenty_range(self):
        data=rows();r=build(data,'1d')
        self.assertEqual((r['high'],r['low']),(220,60))
        self.assertEqual(r['history_candles'],34)
        self.assertFalse(r['cycle_extremes_verified'])
        self.assertFalse(r['bottom_confirmed'])
        self.assertTrue(validate(r,'1d'))
        self.assertNotEqual(r['high'],max(c['high'] for c in data[-21:-1]))

    def test_same_candle_and_confirmation_bar_extremes_not_used(self):
        data=rows();data[3]['low']=1;data[-1].update(high=999,low=.1)
        r=build(data,'1d');self.assertEqual((r['high'],r['low']),(220,60))
        self.assertTrue(r['confirmation_candle_excluded'])

    def test_later_equal_high_restarts_candidate_and_missing_later_low_is_explicit(self):
        data=rows();data[20]['high']=220
        r=build(data,'1d');self.assertNotEqual(r['low'],60)
        data[-2]['high']=220
        self.assertEqual(build(data,'1d')['status'],'unavailable')

    def test_gap_short_history_and_boundary_are_disclosed(self):
        data=rows();data.pop(9)
        self.assertEqual(build(data,'1d')['status'],'unavailable')
        self.assertEqual(build(rows()[:20],'1d')['status'],'unavailable')
        data=rows();data[0]['high']=300
        self.assertTrue(build(data,'1d')['high_at_history_boundary'])

    def test_recomputed_anchor_rejects_changed_extreme(self):
        r=build(rows(),'1d');r['high']+=1
        with self.assertRaisesRegex(ValueError,'anchor disagrees'):validate(r,'1d')

    def test_frozen_v3_remains_valid_and_new_model_discloses_fallback(self):
        # New realistic snapshots get evidence; unchanging fixture highs may use an explicit range fallback.
        feed,now=fixture();r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertTrue(validate_frozen(r))
        self.assertIn(assess(r)['anchor_scope'],('available_history_high_then_later_low','prior20_range_not_confirmed_cycle_ath_or_low'))
        self.assertIn('Ankercontrole',render_meter(r,'swing'))
        r.pop('route_anchors');r['model_version']='two_routes_daily_weekly_v3'
        r['two_route_assessment']=assess(r);r.pop('scenario_set_id')
        r['scenario_set_id']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        self.assertTrue(validate_frozen(r))
