from copy import deepcopy
import unittest

from scripts import elliott_subwaves as sw
from scripts.elliott_dashboard import render_subdivision
from tests.test_elliott_subwaves import fixture, H


def geometry(values,mirror=False):
    values=[400-v for v in values] if mirror else values
    points=[dict(open_time_ms=i*4*H,price=v) for i,v in enumerate(values)]
    rows=[]
    for i,(a,b) in enumerate(zip(values,values[1:])):
        for j in range(4):
            v=a+(b-a)*j/4
            rows.append(dict(open_time_ms=(i*4+j)*H,high=v,low=v))
    rows.append(dict(open_time_ms=12*H,high=values[-1],low=values[-1]))
    return rows,points,'up' if mirror else 'down'


class CorrectionTests(unittest.TestCase):
    def test_expanded_and_running_geometry_in_both_directions_without_certification(self):
        for mirror in (False,True):
            for values,expected in [([150,120,155,110],'expanded_flat_outline'),
                                    ([150,120,155,130],'running_flat_outline'),
                                    ([150,120,140,110],'single_zigzag_outline')]:
                rows,points,direction=geometry(values,mirror);before=deepcopy((rows,points))
                alternatives=sw.correction_outlines(rows,points,direction)
                self.assertEqual([v['family'] for v in alternatives if v['status']=='price_outline_compatible'],[expected])
                self.assertTrue(all(any(c['result']=='niet toetsbaar' for c in v['checks']) for v in alternatives))
                self.assertEqual((rows,points),before)

    def test_boundary_equalities_and_regular_nearness_not_invented_as_flat_rule(self):
        for values in ([150,120,150,110],[150,120,155,120],[150,120,155,155],
                       [150,120,149,125]):
            rows,points,direction=geometry(values)
            flats=sw.correction_outlines(rows,points,direction)[1:]
            self.assertTrue(all(v['status']=='unsupported_correction_outline' for v in flats))

    def test_hidden_wick_blocks_flat_without_replacing_anchor(self):
        for mirror in (False,True):
            rows,points,direction=geometry([150,120,155,110],mirror)
            rows[5]['low']=1
            alternatives=sw.correction_outlines(rows,points,direction)
            self.assertFalse(any(v['status']=='price_outline_compatible' for v in alternatives[1:]))

    def test_real_anchored_completed_parent_and_ui_retain_failed_alternatives(self):
        for mirror in (False,True):
            for fractions,family in [([.6,-.1,1],'expanded_flat_outline'),
                                     ([1.1,-.1,1],'running_flat_outline')]:
                c,p,r,now=fixture(mirror,correction=fractions,stride=8)
                q=sw.assess(c,p,'4h',r,'1h',now)
                self.assertEqual(q['status'],'assessed',q)
                leg=q['legs'][1]
                self.assertEqual(leg.get('compatible_families'),[family],leg)
                self.assertEqual(leg['status'],'price_outline_compatible')
                self.assertEqual(len(leg['correction_alternatives']),3)
                self.assertEqual(leg['points'][0]['price'],c['points'][1]['price'])
                self.assertEqual(leg['points'][-1]['price'],c['points'][2]['price'])
                self.assertEqual(q['wave_certification'],'unproven');self.assertIsNone(q['probability'])
                page=render_subdivision(q)
                self.assertIn('Expanded flat:',page);self.assertIn('Running flat:',page)
                self.assertIn('3-3-5',page);self.assertIn('running flat blijft onbevestigd',page)

    def test_new_family_never_rescues_parent_or_conflicting_source(self):
        c,p,r,now=fixture(correction=[.6,-.1,1],stride=8)
        c['status']='invalid'
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now)['status'],'blocked_invalid_parent')
        c['status']='provisional_price_pattern';r[30]['base_volume_btc']+=1
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now)['status'],'unavailable')

    def test_no_extra_pivots_thinned_or_open_candles_used_for_flat(self):
        c,p,r,now=fixture(correction=[.6,-.1,1],stride=8)
        before=sw.assess(c,p,'4h',r,'1h',now)
        from scripts.market_scenarios import time_ms
        r.append(dict(r[-1],open_time_ms=time_ms(now),low=1,high=9999))
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now),before)
        # Existing full and prefix tests also enforce ALL pivots and fixed-anchor
        # rejection. No new family is run before the exact three-leg gate.
