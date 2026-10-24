from copy import deepcopy
import unittest
from scripts.scenario_path import build_path,render_path
from tests.test_scenario_actions import base_route


def example(direction=1):
    route=base_route()
    route.update(reference_price=115,last_close=115,buffer=1)
    route['fibonacci']={}
    scenario=deepcopy(route['scenarios'][3])
    scenario.update(direction=direction,trigger_price=100 if direction>0 else 130,
                    invalidation_price=95 if direction>0 else 135,
                    targets=[dict(price=130 if direction>0 else 100,kind='range_boundary'),
                             dict(price=140 if direction>0 else 90,kind='atr_projection')],
                    fibonacci_ahead=[dict(price=120 if direction>0 else 110,kind='fib_retracement',ratio=.618)])
    return route,scenario


class ScenarioPathTests(unittest.TestCase):
    def test_origin_and_pretrigger_retracements_are_visible_for_both_directions(self):
        for direction,origin,expected in [(1,80,[80,90,100,120,130,140]),(-1,150,[150,140,130,110,100,90])]:
            r,s=example(direction)
            key='low' if direction>0 else 'high'
            r['fibonacci']={key:origin,key+'_at':'2026-10-01T00:00:00+00:00',
                'anchor_method':'prior20_range_extremes',
                'retracements':[dict(price=90 if direction>0 else 140,ratio=.236)]}
            p=build_path(r,s)
            self.assertEqual([x['price'] for x in p['points']],expected)
            self.assertEqual(p['attention']['price'],120 if direction>0 else 110)
            html=render_path(r,s)
            self.assertIn('Beginprijs',html)
            self.assertIn('2026-10-01T00:00:00+00:00',html)
            self.assertIn('geen vastgestelde all-time high of low',html)
            self.assertEqual(html.count('aria-current="location"'),1)

    def test_invalid_anchor_is_not_invented(self):
        for anchor in [None,float('nan'),float('inf'),True,-1]:
            r,s=example();r['fibonacci']={'low':anchor}
            html=render_path(r,s)
            self.assertIn('Beginprijs ontbreekt',html)

    def test_next_attention_follows_bull_and_bear_direction(self):
        for direction,expected,prices in [(1,120,[100,120,130,140]),(-1,110,[130,110,100,90])]:
            route,scenario=example(direction)
            path=build_path(route,scenario)
            self.assertEqual(path['attention']['price'],expected)
            self.assertEqual([p['price'] for p in path['points']],prices)
            self.assertEqual(path['points'][0]['state'],'beyond')

    def test_nearby_zone_keeps_attention_when_quote_just_crossed(self):
        r,s=example();r['reference_price']=120.5
        p=build_path(r,s)
        self.assertEqual(p['attention']['price'],120)
        self.assertTrue(p['near_attention'])
        self.assertIn('Nu aandacht bij',render_path(r,s))

    def test_duplicate_levels_merge_and_out_of_route_fib_is_excluded(self):
        r,s=example()
        s['fibonacci_ahead'] += [dict(price=130,kind='fib_extension',ratio=1.618),
                                dict(price=150,kind='fib_extension',ratio=2.618)]
        p=build_path(r,s)
        self.assertEqual(len(p['points']),4)
        self.assertEqual(len(p['points'][2]['labels']),2)

    def test_native_invalidation_cancels_next_zone_without_inventing_stop(self):
        r,s=example();r['last_close']=94
        p=build_path(r,s)
        self.assertIsNone(p['attention'])
        html=render_path(r,s)
        self.assertIn('Scenario ongeldig op broncandle-slot',html)
        self.assertNotIn('Volgende aandacht',html)
        self.assertNotIn('stop geraakt',html)

    def test_live_boundary_breach_warns_before_native_invalidation(self):
        r,s=example();r['reference_price']=94
        p=build_path(r,s)
        self.assertFalse(p['invalidated'])
        self.assertTrue(p['live_boundary'])
        self.assertIn('controleer de slotbevestiging',render_path(r,s))

    def test_beyond_last_zone_never_extrapolates_another_target(self):
        r,s=example();r['reference_price']=150
        self.assertIsNone(build_path(r,s)['attention'])
        self.assertIn('geen volgend doel afleiden',render_path(r,s))

    def test_unavailable_price_has_no_path_and_rendering_does_not_mutate_snapshot(self):
        r,s=example();original=deepcopy((r,s))
        html=render_path(r,s)
        self.assertEqual((r,s),original)
        self.assertIn('aria-current="location"',html)
        self.assertIn('geen voorspelde aankomstdatums',html)
        self.assertIn('geen eerdere aanraking',html)
        self.assertIn('shb-levels scenario-path',html)  # included in expiry hiding
        r['reference_price']=None
        self.assertEqual(render_path(r,s),'')
        r['reference_price']=float('nan')
        self.assertIsNone(build_path(r,s))
        r['status']='unavailable'
        self.assertIsNone(build_path(r,s))


if __name__=='__main__':
    unittest.main()
