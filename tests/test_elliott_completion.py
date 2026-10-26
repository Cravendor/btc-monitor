from copy import deepcopy
import unittest
from scripts import elliott_completion as ec
from scripts.elliott_rules import confirmed_pivots
from scripts.market_scenarios import iso

P=14400000
START=1790006400000  # aligned 4H UTC


def rows():
    values=[100,96,90,94,102,112,120,114,108,100,94,88,80,83,87,92,96,94,90,84,78,76,75,74]
    return [dict(open_time_ms=START+i*P,open=v,high=v+.2,low=v-.2,close=v,
                 base_volume_btc=10,quote_volume_usdt=1000) for i,v in enumerate(values)]


def endpoint(data):
    return next(p for p in confirmed_pivots(data[:9]) if p['kind']=='high')


class CompletionTests(unittest.TestCase):
    def test_mirrored_low_endpoint_tracks_bullish_reversal_with_same_stages(self):
        data=rows()
        data=[dict(r,open=300-r['open'],close=300-r['close'],
                   high=300-r['low'],low=300-r['high']) for r in data]
        anchor=next(p for p in confirmed_pivots(data[:9]) if p['kind']=='low')
        for n,stage in [(9,'pivot_only'),(12,'opposing_swing_broken'),
                        (19,'pullback_held'),(21,'continuation_after_pullback')]:
            r=ec.assess(data,'4h',iso(START+n*P),anchor)
            self.assertEqual(r['stage'],stage)
            self.assertEqual(r['reversal_direction'],'up')

    def test_ordered_break_retest_and_continuation_without_wave_certification(self):
        data=rows();anchor=endpoint(data);before=deepcopy(data)
        for n,stage in [(9,'pivot_only'),(12,'opposing_swing_broken'),
                        (19,'pullback_held'),(21,'continuation_after_pullback')]:
            with self.subTest(n=n):
                r=ec.assess(data,'4h',iso(START+n*P),anchor)
                self.assertEqual(r['stage'],stage)
                self.assertEqual(r['opposing_swing']['price'],89.8)
                self.assertEqual(r['wave_completion'],'unproven')
                self.assertIsNone(r['probability'])
                self.assertLessEqual(r['evidence_known_at'],iso(START+n*P))
        self.assertEqual(data,before)

    def test_wicks_invalidate_fixed_endpoint_even_if_candle_closes_in_reversal(self):
        data=rows();anchor=endpoint(data)
        data[20]['high']=121
        r=ec.assess(data,'4h',iso(START+21*P),anchor)
        self.assertEqual(r['stage'],'endpoint_extended')
        self.assertIsNone(r['continuation_at'])

    def test_wick_only_swing_break_is_not_a_close_break(self):
        data=rows()[:12];anchor=endpoint(data)
        data[-1].update(low=80,close=94,open=94,high=95)
        self.assertEqual(ec.assess(data,'4h',iso(START+12*P),anchor)['stage'],'pivot_only')

    def test_equal_retest_does_not_establish_strict_lower_high(self):
        data=rows();anchor=endpoint(data);data[16]['high']=anchor['price']
        r=ec.assess(data,'4h',iso(START+21*P),anchor)
        self.assertEqual(r['stage'],'opposing_swing_broken')
        self.assertIn('pullback_note',r)
        self.assertIsNone(r['continuation_at'])

    def test_open_future_candles_and_future_anchor_cannot_leak_into_reading(self):
        data=rows();anchor=endpoint(data);when=iso(START+12*P)
        before=ec.assess(data,'4h',when,anchor)
        data[12].update(high=999,low=1,close=500,open=100)
        self.assertEqual(ec.assess(data,'4h',when,anchor),before)
        self.assertEqual(ec.assess(data,'4h',iso(START+8*P),anchor)['status'],'unavailable')

    def test_gaps_duplicates_and_unknown_extremum_order_are_not_filled(self):
        data=rows();anchor=endpoint(data)
        for bad in (data[:5]+data[6:],data[:5]+[data[4]]+data[5:]):
            self.assertEqual(ec.assess(bad,'4h',iso(START+24*P),anchor)['status'],'unavailable')
        outside=rows();outside[6]['low']=1
        self.assertEqual(ec.assess(outside,'4h',iso(START+24*P),anchor)['status'],'unavailable')

    def child(self,data):
        result=[]
        for row in data:
            for i in range(4):
                r=dict(row,open_time_ms=row['open_time_ms']+i*P//4,
                       high=row['close']+(.2 if i==1 else .1),
                       low=row['close']-(.2 if i==2 else .1))
                result.append(r)
        return result

    def test_lower_scale_checks_exact_same_parent_extreme(self):
        data=rows();anchor=endpoint(data);now=iso(START+12*P)
        parent=ec.assess(data,'4h',now,anchor)
        child=ec.lower_evidence(parent,self.child(data),'1h',now)
        self.assertEqual(child['status'],'available')
        self.assertEqual(child['endpoint']['price'],anchor['price'])
        self.assertEqual(child['endpoint']['open_time_ms'],anchor['open_time_ms']+P//4)
        self.assertEqual(child['parent_anchor_at'],iso(anchor['open_time_ms']))
        self.assertEqual(child['wave_completion'],'unproven')

    def test_ambiguous_child_extreme_missing_coverage_or_blocked_parent_stay_unavailable(self):
        data=rows();anchor=endpoint(data);now=iso(START+12*P)
        parent=ec.assess(data,'4h',now,anchor);child=self.child(data)
        repeated=deepcopy(child);repeated[6*4+2]['high']=anchor['price']
        conflicting=deepcopy(child);conflicting[6*4]['high']=anchor['price']+10
        for source in (repeated,conflicting,child[:6*4]+child[6*4+1:]):
            self.assertEqual(ec.lower_evidence(parent,source,'1h',now)['status'],'unavailable')
        self.assertEqual(ec.lower_evidence({'status':'unavailable'},child,'1h',now)['status'],'unavailable')
        future=deepcopy(parent);future['endpoint']['confirmed_at_ms']=START+13*P
        self.assertEqual(ec.lower_evidence(future,child,'1h',now)['status'],'unavailable')
