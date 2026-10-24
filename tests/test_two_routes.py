from copy import deepcopy
import hashlib
import json
import unittest
from tests.test_scenario_actions import base_route
from scripts.two_routes import assess, combination, render_meter
from scripts.swing_scenarios import validate_frozen


class TwoRouteTests(unittest.TestCase):
    def route(self):
        r=base_route()
        r['fibonacci'].update(status='calculated',low=100,high=200,
            anchor_method='prior20_range_extremes',low_at='2026-09-01T00:00:00Z',high_at='2026-10-01T00:00:00Z')
        r['reference_price']=124
        r['buffer']=.2
        r['level_assessment'].update(confirmation_bar=dict(open=126,low=122,high=128,close=127),
            confirmation_previous_close=128,confirmation_prior_close=130)
        r['momentum']['score']=2
        return r

    def test_all_25_have_stable_distinct_ids_and_global_direction(self):
        pairs=[combination(b,s) for b in range(-2,3) for s in range(-2,3)]
        self.assertEqual(len({x['id'] for x in pairs}),25)
        self.assertEqual(combination(2,2)['score'],2)
        self.assertEqual(combination(-2,-2)['score'],-2)
        self.assertEqual(combination(2,-1)['score'],0)
        self.assertIn('Tegengestelde',combination(2,-1)['label'])
        self.assertEqual(combination(1,0)['score'],1)
        self.assertIsNone(combination(1,None)['score'])
        for value in (True,3,'BUY'):
            with self.assertRaises(ValueError):combination(value,0)

    def test_separate_ladders_and_same_buy_meaning(self):
        data=assess(self.route())
        bull,bear=data['routes']
        self.assertEqual(bull['origin_price'],100)
        self.assertEqual(bear['origin_price'],200)
        self.assertNotEqual(bull['selected_zone'],bear['selected_zone'])
        self.assertEqual(bull['score'],2)
        self.assertFalse(data['independent_evidence'])
        r=self.route();r['reference_price']=178
        r['level_assessment'].update(confirmation_bar=dict(open=178,low=174,high=179,close=179),confirmation_previous_close=180)
        self.assertGreater(assess(r)['routes'][1]['score'],0)  # BUY in BEAR route is upward.

    def test_no_test_or_live_conflict_is_not_a_confirmed_signal(self):
        r=self.route();r['level_assessment']['confirmation_bar']=dict(open=140,low=139,high=141,close=140)
        self.assertEqual([x['score'] for x in assess(r)['routes']],[0,0])
        r=self.route();r['reference_price']=122
        self.assertEqual(assess(r)['routes'][0]['score'],0)

    def test_retest_requires_prior_crossing_of_same_zone(self):
        r=self.route()
        self.assertFalse(assess(r)['routes'][0]['retest_observed'])
        r['level_assessment']['confirmation_prior_close']=120
        result=assess(r)
        self.assertTrue(result['routes'][0]['retest_observed'])
        self.assertIn('terugtest',result['context'])
        r['level_assessment'].pop('confirmation_prior_close')
        self.assertFalse(assess(r)['routes'][0]['retest_observed'])

    def test_missing_data_not_neutral_and_ui_has_two_paths(self):
        r=self.route();html=render_meter(r,'swing')
        self.assertEqual(html.count('aria-current="location"'),2)
        self.assertIn('25 combinaties',html)
        self.assertIn('cyclus-ATH/bodem nog niet bevestigd',html)
        r['reference_price']=None
        self.assertIsNone(assess(r)['combined']['score'])
        self.assertNotIn('gauge-needle',render_meter(r,'swing'))

    def test_frozen_assessment_recomputed_even_after_rehash(self):
        from tests.test_price_roadmap import fixture
        from scripts.swing_scenarios import build_swing_scenarios
        feed,now=fixture();r=build_swing_scenarios(feed,now)['horizons']['swing']
        self.assertTrue(validate_frozen(r))
        r['two_route_assessment']['context']='changed after the fact'
        r.pop('scenario_set_id')
        r['scenario_set_id']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        with self.assertRaisesRegex(ValueError,'two-route assessment'):validate_frozen(r)
