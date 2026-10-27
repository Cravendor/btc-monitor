from copy import deepcopy
import unittest
from scripts import elliott_candidates as ec
from scripts.elliott_rules import confirmed_pivots
from scripts.elliott_dashboard import render_forming_candidates, build as dashboard
from scripts.market_scenarios import iso

P=14400000
START=1790006400000


def source(targets=(100,130,115,170,145)):
    values=[110,105]
    for a,b in zip(targets,targets[1:]):
        values.extend([a+(b-a)*i/4 for i in range(4)])
    values.extend([targets[-1],targets[-1]+5,targets[-1]+10])
    return [dict(open_time_ms=START+i*P,open=v,high=v+.1,low=v-.1,close=v,
                 base_volume_btc=10,quote_volume_usdt=1000) for i,v in enumerate(values)]


def assess(data, as_of=None):
    return ec.build(data,'4h',as_of or iso(data[-1]['open_time_ms']+P))


class CandidateInventoryTests(unittest.TestCase):
    def test_all_latest_suffixes_retained_without_selecting_passing_counts(self):
        data=source();before=deepcopy(data);r=assess(data);pivots=confirmed_pivots(data)
        self.assertEqual(r['scope'],'current_closed_window')
        self.assertEqual([c['completed_pivot_legs'] for c in r['candidates']],[1,2,3,4])
        for n,c in enumerate(r['candidates'],2):
            self.assertEqual(c['points'],pivots[-n:])
            self.assertIsNone(c['probability'])
            self.assertEqual(c['wave_certification'],'unproven')
        last=r['candidates'][-1]
        self.assertEqual(last['status'],'unresolved_price_prefix')
        self.assertEqual(last['proposed_live_leg'],5)
        self.assertEqual(last['proposed_live_direction'],'up')
        self.assertFalse(last['live_extreme']['confirmed'])
        self.assertIsNone(r['preferred_id']);self.assertIsNone(r['current_wave'])
        self.assertEqual(data,before)

    def test_mirrored_bearish_pattern_uses_symmetric_price_rules(self):
        data=source()
        mirrored=[dict(r,open=400-r['open'],close=400-r['close'],
                       high=400-r['low'],low=400-r['high']) for r in data]
        a,b=assess(data)['candidates'][-1],assess(mirrored)['candidates'][-1]
        self.assertEqual(b['direction'],'down');self.assertEqual(b['proposed_live_direction'],'down')
        self.assertEqual(a['status'],b['status'])
        self.assertEqual([(x['rule'],x['result']) for x in a['checks']],
                         [(x['rule'],x['result']) for x in b['checks']])

    def test_live_corrective_wick_invalidates_even_with_recovering_close(self):
        data=source((100,130,115,170))
        # Final high pivot followed by a falling leg, no confirmed fourth low.
        data[-2].update(open=165,high=166,low=160,close=165)
        data[-1].update(open=164,high=165,low=129,close=164)
        r=assess(data)['candidates'][-1]
        self.assertEqual(r['proposed_live_leg'],4)
        self.assertEqual(r['status'],'invalid')
        self.assertEqual(next(x['result'] for x in r['checks'] if x['rule']=='lopend_4_geen_overlap_1'),'geschonden')

    def test_fixed_endpoint_extension_invalidates_without_rewriting_id(self):
        data=source();a=assess(data)['candidates'][-1]
        data.append(dict(data[-1],open_time_ms=data[-1]['open_time_ms']+P,low=140,high=160,open=155,close=155))
        b=assess(data)['candidates'][-1]
        self.assertEqual(a['id'],b['id'])
        self.assertEqual(b['status'],'invalid')
        self.assertEqual(next(x['result'] for x in b['checks'] if x['rule']=='vast_eindanker'),'geschonden')

    def test_wave_three_shortest_rejected_as_live_fifth_exceeds_it(self):
        data=source((100,150,130,165,155))
        data[-1].update(high=195,close=190,open=165)
        r=assess(data)['candidates'][-1]
        self.assertEqual(r['status'],'invalid')
        self.assertEqual(next(x['result'] for x in r['checks'] if x['rule']=='lopend_5_golf_3_niet_kortste'),'geschonden')

    def test_only_two_pivots_does_not_pass_unformed_third_length_rule(self):
        data=source((100,130));data[-2].update(open=125,close=125,high=126,low=124)
        data[-1].update(open=120,close=120,high=121,low=119)
        r=assess(data)['candidates'][0]
        self.assertEqual(r['completed_pivot_legs'],1)
        self.assertEqual(next(x['result'] for x in r['checks'] if x['rule']=='golf_3_niet_kortste'),'niet toetsbaar')

    def test_open_future_data_does_not_leak_and_ids_persist_on_unchanged_anchors(self):
        data=source();when=iso(data[-1]['open_time_ms']+P);a=assess(data,when)
        future=dict(data[-1],open_time_ms=data[-1]['open_time_ms']+P,high=999,low=1)
        self.assertEqual(a,assess(data+[future],when))
        future.update(high=160,low=150,open=155,close=155)
        b=assess(data+[future])
        self.assertEqual([c['id'] for c in a['candidates']],[c['id'] for c in b['candidates']])
        self.assertNotEqual(a['closed_through'],b['closed_through'])

    def test_gap_duplicate_invalid_volume_and_historical_scope_are_explicit(self):
        data=source()
        for bad in (data[:5]+data[6:],data[:5]+[data[4]]+data[5:]):
            self.assertEqual(assess(bad)['status'],'unavailable')
        bad=deepcopy(data);bad[4]['base_volume_btc']=None
        self.assertEqual(assess(bad)['status'],'unavailable')
        r=assess(data,iso(data[-1]['open_time_ms']+2*P))
        self.assertEqual(r['scope'],'historical_closed_window')
        self.assertIn('HISTORISCH',render_forming_candidates(r))
        empty=ec.build([],'4h',iso(START))
        self.assertEqual(empty['status'],'unavailable');self.assertEqual(empty['candidates'],[])

    def test_dashboard_discloses_anchors_violations_and_limited_family(self):
        r=assess(source());html=render_forming_candidates(r)
        for text in ('Lopende impulsvoorstellen','standaardimpulsen','ONGELDIG','geen bevestigde Elliott-labels','Geen voorkeur of kanspercentage','nog niet als vaste historie'):
            self.assertIn(text,html)
        self.assertIn(r['candidates'][-1]['id'],html)
        # A source-conflicted timeframe never gets an inventory via another scale.
        history={'4h':dict(status='conflict',rows=source())}
        b=dashboard({},iso(START+24*P),history)
        h=next(x for x in b['horizons'] if x['timeframe']=='4h')
        self.assertEqual(h['status'],'unavailable');self.assertNotIn('forming_candidates',h)
