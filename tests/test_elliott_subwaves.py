from copy import deepcopy
import unittest
from scripts import elliott_subwaves as sw
from scripts.elliott_rules import price_checks
from scripts.market_scenarios import iso

H=3600000
START=1790006400000


def fixture(mirror=False):
    targets=[100,130,115,170,145,190]
    vertices=[(14,targets[0])];anchors=[14]
    for n,(a,b) in enumerate(zip(targets,targets[1:]),1):
        fractions=[.35,.2,.75,.6,1] if n%2 else [.6,.3,1]
        begin=vertices[-1][0]
        for j,x in enumerate(fractions,1):vertices.append((begin+j*4,a+(b-a)*x))
        anchors.append(vertices[-1][0])
    lookup=dict(vertices);last=vertices[-1][0];rows=[]
    for i in range(last+15):
        if i<14:v=100+(14-i)
        elif i>last:v=190-(i-last)
        else:
            a,b=next((a,b) for a,b in zip(vertices,vertices[1:]) if a[0]<=i<=b[0])
            v=a[1]+(b[1]-a[1])*(i-a[0])/(b[0]-a[0])
        high,low,close=v+.01,v-.01,v
        if i in lookup:
            j=[x[0] for x in vertices].index(i)
            if j%2:high,low,close=v,v-.1,v-.05
            else:high,low,close=v+.1,v,v+.05
        rows.append(dict(open_time_ms=START+i*H,open=close,close=close,high=high,low=low,
                         base_volume_btc=1,quote_volume_usdt=100))
    if mirror:
        rows=[dict(r,open=400-r['open'],close=400-r['close'],high=400-r['low'],low=400-r['high']) for r in rows]
    parents=[]
    for i in range(0,len(rows)-3,4):
        piece=rows[i:i+4]
        parents.append(dict(open_time_ms=piece[0]['open_time_ms'],open=piece[0]['open'],close=piece[-1]['close'],
                            high=max(r['high'] for r in piece),low=min(r['low'] for r in piece),
                            base_volume_btc=4,quote_volume_usdt=400))
    points=[dict(open_time_ms=START+(i//4*4)*H,price=400-v if mirror else v,
                 kind=('high' if j%2==0 else 'low') if mirror else ('low' if j%2==0 else 'high'),
                 confirmed_at_ms=START+(i//4*4+12)*H) for j,(i,v) in enumerate(zip(anchors,targets))]
    candidate=dict(id='fixed',pattern='standard_impulse',status='provisional_price_pattern',
                   direction='down' if mirror else 'up',points=points)
    now=iso(parents[-1]['open_time_ms']+4*H)
    return candidate,parents,rows,now


class SubwaveTests(unittest.TestCase):
    def rewrite_first_leg(self,rows,vertices):
        changed=deepcopy(rows)
        for i in range(vertices[0][0],vertices[-1][0]+1):
            a,b=next((a,b) for a,b in zip(vertices,vertices[1:]) if a[0]<=i<=b[0])
            v=a[1]+(b[1]-a[1])*(i-a[0])/(b[0]-a[0]);close=v;hi=v+.01;lo=v-.01
            if i in dict(vertices):
                j=[x[0] for x in vertices].index(i)
                hi,lo,close=(v,v-.1,v-.05) if j%2 else (v+.1,v,v+.05)
            changed[i].update(open=close,close=close,high=hi,low=lo)
        parents=[]
        for i in range(0,len(changed)-3,4):
            piece=changed[i:i+4]
            parents.append(dict(open_time_ms=piece[0]['open_time_ms'],open=piece[0]['open'],close=piece[-1]['close'],
                                high=max(r['high'] for r in piece),low=min(r['low'] for r in piece),
                                base_volume_btc=4,quote_volume_usdt=400))
        return parents,changed

    def test_exact_shared_anchors_have_5_3_5_3_5_outlines_in_both_directions(self):
        for mirror in (False,True):
            c,p,r,now=fixture(mirror);before=deepcopy((c,p,r))
            self.assertFalse(any(x['result']=='geschonden' for x in price_checks(p,c['points'],c['direction'])))
            q=sw.assess(c,p,'4h',r,'1h',now)
            self.assertEqual(q['status'],'assessed',q)
            self.assertEqual(q['price_subdivision_status'],'compatible_outlines',q)
            self.assertEqual([x['observed_legs'] for x in q['legs']],[5,3,5,3,5])
            self.assertEqual(q['compatible_legs'],5)
            self.assertEqual(q['wave_certification'],'unproven')
            self.assertIsNone(q['probability'])
            for i,l in enumerate(q['legs']):
                self.assertEqual(l['points'][0]['price'],c['points'][i]['price'])
                self.assertEqual(l['points'][-1]['price'],c['points'][i+1]['price'])
                self.assertTrue(any(x['result']=='niet toetsbaar' for x in l['checks']))
            self.assertEqual((c,p,r),before)

    def test_invalid_parent_cannot_be_rescued_and_parent_rules_are_rechecked(self):
        c,p,r,now=fixture();c['status']='invalid'
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now)['status'],'blocked_invalid_parent')
        c['status']='provisional_price_pattern';c['points'][4]['price']=120
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now)['status'],'blocked_invalid_parent')
        c['status']='unknown'
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now)['status'],'unavailable')

    def test_wrong_internal_impulse_not_just_endpoint_count_is_rejected(self):
        c,p,r,now=fixture()
        # Keep six child pivots, but violate internal wave-4/1 overlap.
        p,r=self.rewrite_first_leg(r,[(14,100),(18,110.5),(22,106),(26,122.5),(30,109),(34,130)])
        q=sw.assess(c,p,'4h',r,'1h',now)
        self.assertEqual(q['status'],'assessed',q)
        self.assertEqual(q['legs'][0]['observed_legs'],5)
        self.assertEqual(q['legs'][0]['status'],'price_rules_violated')
        self.assertTrue(any(x['rule']=='golf_4_geen_overlap_1' and x['result']=='geschonden' for x in q['legs'][0]['checks']))

    def test_more_internal_pivots_are_not_skipped_to_force_five(self):
        c,p,r,now=fixture()
        p,r=self.rewrite_first_leg(r,[(14,100),(18,110.5),(20,108),(22,112),(24,110),(26,122.5),(30,118),(34,130)])
        q=sw.assess(c,p,'4h',r,'1h',now)
        self.assertEqual(q['status'],'assessed',q)
        self.assertEqual(q['legs'][0]['observed_legs'],7)
        self.assertEqual(q['legs'][0]['reason'],'different_or_unresolved_child_degree')
        self.assertEqual(q['legs'][0]['status'],'unresolved')

    def test_open_child_candle_cannot_change_historical_outline(self):
        c,p,r,now=fixture();before=sw.assess(c,p,'4h',r,'1h',now)
        from scripts.market_scenarios import time_ms
        r=[x for x in r if x['open_time_ms']<time_ms(now)]
        r.append(dict(r[-1],open_time_ms=time_ms(now),high=999,low=1))
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',now),before)

    def test_render_shows_anchored_points_and_limit_even_when_all_outlines_fit(self):
        from scripts.elliott_dashboard import render_subdivision
        c,p,r,now=fixture();q=sw.assess(c,p,'4h',r,'1h',now)
        page=render_subdivision(q)
        self.assertIn('5 van 5',page)
        self.assertIn('geen gecertificeerde Elliott-telling',page)
        self.assertIn('Lagere pivots en regels',page)
        self.assertIn(q['legs'][0]['mapped_start_at'],page)
        self.assertIn('Getoetst: 5',page)
        c['status']='invalid'
        self.assertIn('Onderverdeling geblokkeerd',render_subdivision(sw.assess(c,p,'4h',r,'1h',now)))

    def test_future_parent_confirmation_and_missing_or_conflicting_sources_are_unavailable(self):
        c,p,r,now=fixture()
        early=iso(c['points'][-1]['confirmed_at_ms']-H)
        self.assertEqual(sw.assess(c,p,'4h',r,'1h',early)['status'],'unavailable')
        for child in (r[:25]+r[26:],r[:25]+[r[24]]+r[25:]):
            self.assertEqual(sw.assess(c,p,'4h',child,'1h',now)['status'],'unavailable')
        changed=deepcopy(p);changed[5]['base_volume_btc']=5
        self.assertEqual(sw.assess(c,changed,'4h',r,'1h',now)['status'],'unavailable')

    def test_extra_degree_is_not_thinned_to_fit_and_ambiguous_anchor_not_guessed(self):
        c,p,r,now=fixture()
        # Repeated exact parent low inside the same native anchor candle.
        changed=deepcopy(r);changed[13]['low']=100
        # Keep parent aggregate equal: only uniqueness should block adjacent leg.
        q=sw.assess(c,p,'4h',changed,'1h',now)
        self.assertEqual(q['status'],'assessed',q)
        self.assertEqual(q['legs'][0]['status'],'unresolved')
        self.assertIn('ambiguous',q['legs'][0]['reason'])
        self.assertLess(q['compatible_legs'],5)

    def test_other_corrections_are_unsupported_not_a_universal_invalid_label(self):
        pts=[dict(open_time_ms=i*H,price=v) for i,v in enumerate([150,120,155,110])]
        rows=[dict(open_time_ms=i*H,high=v,low=v) for i,v in enumerate([150,120,155,110])]
        checks=sw.zigzag_checks(rows,pts,'down')
        self.assertTrue(any(x['result']=='geschonden' for x in checks))
        self.assertTrue(any(x['result']=='niet toetsbaar' for x in checks))

    def test_expanded_flat_endpoints_in_both_directions_and_strict_boundaries(self):
        for direction,values in [('down',[150,120,155,110]),('up',[150,180,145,190])]:
            def check(v):
                return sw.expanded_flat_checks([{'price':x} for x in v],direction)
            result=check(values)
            self.assertFalse(any(c['result']=='geschonden' for c in result))
            self.assertEqual(result[-1]['result'],'niet toetsbaar')
            points=[dict(open_time_ms=i*H,price=v) for i,v in enumerate(values)]
            rows=[dict(open_time_ms=i*H,high=v,low=v) for i,v in enumerate(values)]
            family,selected=sw.correction_outline(rows,points,direction)
            self.assertEqual(family,'expanded_flat_endpoint_outline')
            self.assertEqual(selected,result)
            for index,replacement in [(2,values[0]),(3,values[1])]:
                boundary=values.copy();boundary[index]=replacement
                self.assertTrue(any(c['result']=='geschonden' for c in check(boundary)))

    def test_expanded_flat_dashboard_does_not_claim_certification(self):
        from scripts.elliott_dashboard import render_subdivision
        c,p,r,now=fixture();q=sw.assess(c,p,'4h',r,'1h',now)
        q['legs'][1]['family']='expanded_flat_endpoint_outline'
        q['legs'][1]['checks']=sw.expanded_flat_checks(
            [{'price':x} for x in [150,120,155,110]],'down')
        page=render_subdivision(q)
        self.assertIn('Expanded flat: alleen eindpunten',page)
        self.assertIn('interne_A_B_C_3_3_5: niet toetsbaar',page)
        self.assertIn('geen gecertificeerde Elliott-telling',page)
