from copy import deepcopy
import unittest
from tests.test_elliott_subwaves import fixture,H,START
from scripts.elliott_candidates import build as inventory
from scripts.elliott_completion import closed_rows
from scripts.elliott_subwaves import assess_prefix
from scripts.elliott_dashboard import build,render_forming_candidates
from scripts.market_scenarios import iso


def prefix(n=4,mirror=False):
    c,p,r,_=fixture(mirror)
    now=iso(c['points'][n]['confirmed_at_ms'])
    q=next(x for x in inventory(p,'4h',now)['candidates'] if x['completed_pivot_legs']==n)
    return q,p,r,now


class PrefixLinkTests(unittest.TestCase):
    def test_one_to_four_formed_legs_share_exact_anchors_in_both_directions(self):
        for mirror in (False,True):
            for n in range(1,5):
                with self.subTest(mirror=mirror,n=n):
                    c,p,r,now=prefix(n,mirror);before=deepcopy((c,p,r))
                    q=assess_prefix(c,p,'4h',r,'1h',now)
                    self.assertEqual(q['status'],'assessed',q)
                    self.assertEqual(q['formed_legs'],n)
                    self.assertEqual(q['compatible_legs'],n)
                    self.assertEqual([l['observed_legs'] for l in q['legs']],[5,3,5,3][:n])
                    self.assertEqual(q['ongoing_leg'],n+1)
                    self.assertEqual(q['ongoing_leg_status'],'unconfirmed_parent_endpoint_not_tested')
                    self.assertEqual(q['wave_certification'],'unproven');self.assertIsNone(q['probability'])
                    for i,leg in enumerate(q['legs']):
                        self.assertEqual(leg['points'][0]['price'],c['points'][i]['price'])
                        self.assertEqual(leg['points'][-1]['price'],c['points'][i+1]['price'])
                    self.assertEqual((c,p,r),before)

    def test_invalid_parent_stays_blocked_even_if_caller_claims_it_passes(self):
        c,p,r,now=prefix(3)
        bad=next(x for x in inventory(p,'4h',now)['candidates'] if x['status']=='invalid')
        self.assertEqual(assess_prefix(bad,p,'4h',r,'1h',now)['status'],'blocked_invalid_parent')
        bad['status']='unresolved_price_prefix'
        self.assertEqual(assess_prefix(bad,p,'4h',r,'1h',now)['status'],'blocked_invalid_parent')

    def test_forged_or_future_anchors_and_obsolete_suffix_ids_not_accepted(self):
        c,p,r,now=prefix(2)
        changed=deepcopy(c);changed['points'][0]['price']+=1
        future=deepcopy(c);future['points'][-1]['confirmed_at_ms']+=100*H
        unknown=deepcopy(c);unknown['id']='invented'
        for bad in [changed,future,unknown]:
            self.assertEqual(assess_prefix(bad,p,'4h',r,'1h',now)['status'],'unavailable')
        _,_,_,later=prefix(4)
        self.assertEqual(assess_prefix(c,p,'4h',r,'1h',later)['status'],'unavailable')

    def test_source_disagreement_gap_duplicate_and_missing_group_not_linked(self):
        c,p,r,now=prefix(2)
        revised=deepcopy(r);revised[16]['base_volume_btc']+=1
        for bad in [revised,r[:16]+r[17:],r[:16]+[r[15]]+r[16:],r[16:]]:
            self.assertEqual(assess_prefix(c,p,'4h',bad,'1h',now)['status'],'unavailable')

    def test_tied_child_extreme_remains_unresolved_instead_of_changing_parent_anchor(self):
        c,p,r,now=prefix(1);changed=deepcopy(r);changed[13]['low']=100
        q=assess_prefix(c,p,'4h',changed,'1h',now)
        self.assertEqual(q['status'],'assessed')
        self.assertEqual(q['legs'][0]['status'],'unresolved')
        self.assertEqual(q['legs'][0]['reason'],'parent_extreme_ambiguous_or_missing')
        self.assertEqual(q['compatible_legs'],0)

    def test_future_open_child_candles_cannot_change_historical_link(self):
        c,p,r,now=prefix(2);before=assess_prefix(c,p,'4h',r,'1h',now)
        changed=deepcopy(r)
        for row in changed:
            if row['open_time_ms']>=c['points'][-1]['confirmed_at_ms']:
                row.update(high=9999,low=1,open=100,close=100)
        self.assertEqual(assess_prefix(c,p,'4h',changed,'1h',now),before)

    def test_dashboard_links_formed_legs_and_discloses_ongoing_leg_without_certifying(self):
        c,p,r,_=prefix(4);now=iso(c['points'][-1]['confirmed_at_ms']+8*H)
        history={tf:dict(status='complete',rows=closed_rows(rows,tf,now),source_at=now,source_path='fixture.json') for tf,rows in [('4h',p),('1h',r)]}
        b=build({},now,history);h=next(x for x in b['horizons'] if x['timeframe']=='4h')
        self.assertEqual(h['status'],'available')
        q=next(x for x in h['forming_candidates']['candidates'] if x['completed_pivot_legs']==4)
        e=h['forming_subdivision_evidence'][q['id']]
        self.assertEqual(e['compatible_legs'],4)
        html=render_forming_candidates(h['forming_candidates'],h)
        self.assertIn('Gevormde hogere benen: 4',html)
        self.assertIn('Lopend hoger been 5?',html)
        self.assertIn('geen bevestigd eindanker',html)
        self.assertIsNone(b['current_wave'])
        # Blocked source is never replaced by the adjacent available child scale.
        history['4h']['status']='conflict'
        b=build({},now,history);h=next(x for x in b['horizons'] if x['timeframe']=='4h')
        self.assertEqual(h['status'],'unavailable')
        self.assertNotIn('forming_subdivision_evidence',h)
