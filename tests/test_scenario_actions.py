from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from tests.test_price_roadmap import fixture
from tests.test_swing_scenarios import directional,frozen_record
from tests import test_swing_scenarios as scenario_tests
from scripts.swing_scenarios import build_swing_scenarios,validate_frozen
from scripts.scenario_actions import assess_action,branches
from scripts.shb_dashboard import gauge_action,render_meter
from scripts.scenario_evaluation import evaluate,build


def base_route():
    feed,now=fixture();feed=directional(feed)
    route=build_swing_scenarios(feed,now)['horizons']['swing']
    # Isolate signal-rule tests from incidental confirmation-candle fixtures.
    route['level_assessment']['confirmation_bar']=dict(open=115,high=120,low=114,close=119)
    route['level_assessment']['confirmation_previous_close']=115
    route['level_assessment']['selected']=None
    route['level_assessment']['reaction']='not_tested'
    return route


class ScenarioActionTests(unittest.TestCase):
    def test_every_proposed_route_has_frozen_shb_and_four_subroutes(self):
        feed,now=fixture();r=build_swing_scenarios(feed,now)
        for route in r['horizons'].values():
            self.assertEqual(set(route['scenario_actions']),{s['id'] for s in route['scenarios']})
            self.assertTrue(validate_frozen(route))
            for s in route['scenarios']:
                action=route['scenario_actions'][s['id']]
                self.assertFalse(action['automatic_execution'])
                self.assertFalse(action['position_tracked'])
                self.assertFalse(action['hard_stop_verified'])
                self.assertTrue(s['furthest_is_conditional'])
                self.assertEqual([b['id'] for b in s['branches']],['continuation','retest','pause','counter_reaction'])

    def test_new_bull_confirmation_buy_then_no_new_action_hold(self):
        r=base_route();s=r['scenarios'][3]
        self.assertEqual(assess_action(r,s)['action'],'BUY')
        r['previous_close']=115
        result=assess_action(r,s)
        self.assertEqual(result['action'],'HOLD')
        self.assertIn('geen nieuwe',result['reason'].lower())

    def test_reached_target_does_not_automatically_buy_toward_extreme(self):
        r=base_route();s=r['scenarios'][3]
        r['reference_price']=140
        result=assess_action(r,s)
        self.assertEqual(result['action'],'HOLD')
        self.assertIn('opnieuw',result['reason'])
        self.assertFalse(result['automatic_execution'])

    def test_target_rejection_and_native_invalidation_are_separate(self):
        r=base_route();s=r['scenarios'][3]
        r['level_assessment']['confirmation_bar']=dict(open=130,high=134,low=120,close=125)
        result=assess_action(r,s)
        self.assertEqual(result['action'],'SELL')
        self.assertTrue(result['criteria']['counter_reaction_at_target'])
        self.assertFalse(result['criteria']['native_close_invalidated'])
        r=base_route();r['previous_close']=115;r['last_close']=107;r['reference_price']=107
        result=assess_action(r,r['scenarios'][3])
        self.assertEqual(result['action'],'SELL')
        self.assertTrue(result['criteria']['native_close_invalidated'])

    def test_untriggered_or_live_conflicting_scenario_waits(self):
        r=base_route();s=r['scenarios'][3]
        r['reference_price']=105
        self.assertEqual(assess_action(r,s)['action'],'WAIT')
        r['reference_price']=100;r['last_close']=100
        self.assertEqual(assess_action(r,s)['action'],'WAIT')
        r['reference_price']=None
        self.assertIsNone(assess_action(r,s)['action'])

    def test_bear_momentum_can_coexist_with_hold_in_selected_bull_case(self):
        r=base_route();s=r['scenarios'][3]
        r['previous_close']=115;r['last_close']=111;r['reference_price']=113
        r['momentum']['score']=-1;s['currently_supported']=False
        result=assess_action(r,s)
        self.assertEqual(result['action'],'HOLD')
        self.assertFalse(result['hard_stop_verified'])

    def test_bearish_route_sell_and_target_bounce_reassessment(self):
        r=base_route();s=r['scenarios'][0]
        r.update(last_close=85,previous_close=100,reference_price=85)
        s['currently_supported']=True
        r['level_assessment']['confirmation_bar']=dict(open=88,high=89,low=80,close=85)
        self.assertEqual(assess_action(r,s)['action'],'SELL')
        r['level_assessment']['confirmation_bar']=dict(open=70,high=75,low=65,close=74)
        self.assertEqual(assess_action(r,s)['action'],'HOLD')

    def test_no_preference_still_proposes_four_routes_and_waits(self):
        r=base_route();r['preferred_scenario']=None
        self.assertEqual(gauge_action(r)['action'],'WAIT')
        self.assertEqual(len(r['scenarios']),4)
        self.assertIsNotNone(gauge_action(r,'bullish')['scenario_id'])
        self.assertIsNone(gauge_action({'status':'unavailable'})['action'])

    def test_branches_do_not_assume_extreme_and_retest_requires_prior_break(self):
        r=base_route();s=r['scenarios'][3]
        r['level_assessment']['confirmation_bar']=dict(open=130,high=134,low=125,close=130)
        items=branches(r,s)
        self.assertTrue(items[2]['observed'])
        self.assertFalse(items[0]['observed'])
        r['level_assessment']['confirmation_bar']=dict(open=112,high=114,low=110,close=113)
        r['level_assessment']['confirmation_previous_close']=110
        self.assertFalse(branches(r,s)[1]['observed'])
        r['level_assessment']['confirmation_previous_close']=115
        self.assertTrue(branches(r,s)[1]['observed'])

    def test_render_scenario_identity_levels_wait_and_no_private_inputs(self):
        r=base_route();html=render_meter(r,'swing')
        self.assertEqual(html.count('<article class="meter"'),1)
        self.assertEqual(html.count('class="shb-case"'),5)
        self.assertIn('data-scenario-case="auto"',html)
        self.assertIn('data-scenario-case="bullish" hidden',html)
        self.assertIn('Ongeldigverklaring',html)
        self.assertIn('geen eigen positie',html)
        self.assertNotIn('<input',html)

    def test_original_shb_is_evaluated_and_old_snapshots_not_rebuilt(self):
        records,end=scenario_tests.EvaluationTests().series()
        rows=evaluate(records,end,7)
        self.assertTrue(all(row['original_shb'] is not None for row in rows if 'route' in row))
        initial=deepcopy(records[0])
        route=initial[0]['scenario_snapshot']['horizons']['swing']
        route.pop('scenario_actions')
        route['model_version']='four_routes_daily_weekly_v1'
        # Existing older schema-1 sets remain recognizable only with their own valid ID.
        import hashlib
        route.pop('scenario_set_id')
        route['scenario_set_id']=hashlib.sha256(json.dumps(route,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        result=evaluate([initial],initial[0]['finished_at'],7)
        self.assertTrue(all(x['original_shb'] is None for x in result if x.get('mode')=='swing'))


class IntermediateZoneTests(unittest.TestCase):
    def test_fib_rejection_can_pause_the_larger_bull_route(self):
        r=base_route();s=r['scenarios'][3]
        r['level_assessment'].update(selected=dict(price=120,kind='fib_retracement'),reaction='rejection')
        result=assess_action(r,s)
        self.assertEqual(result['action'],'SELL')
        self.assertTrue(result['criteria']['intermediate_counter_reaction'])
        self.assertFalse(result['criteria']['native_close_invalidated'])

    def test_fib_support_and_target_reached_are_not_equivalent(self):
        r=base_route();s=r['scenarios'][3]
        r['reference_price']=125;r['previous_close']=115
        r['level_assessment'].update(selected=dict(price=120,kind='fib_retracement'),reaction='support_hold')
        self.assertEqual(assess_action(r,s)['action'],'BUY')
        r['reference_price']=140
        self.assertEqual(assess_action(r,s)['action'],'HOLD')


class SemanticQualityTests(unittest.TestCase):
    def test_rehashed_wrong_shb_does_not_pass_rule_control(self):
        import hashlib
        r=base_route()
        r['scenario_actions']['very_bullish']['action']='SELL'
        r.pop('scenario_set_id')
        r['scenario_set_id']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        with self.assertRaisesRegex(ValueError,'SHB assessment'):validate_frozen(r)
