from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from scripts.momentum_confirmation import build, render, previous_record, PERIOD
from scripts.market_scenarios import time_ms, iso


def fixture(down=False):
    end=time_ms('2026-10-26T08:00:00Z')
    closes=[100]*25+[103,102,101,100,104]
    if down: closes=[200-x for x in closes]
    rows=[dict(open_time_ms=end-(30-i)*PERIOD,open=c,high=c+.5,low=c-.5,close=c,base_volume_btc=20,quote_volume_usdt=2000) for i,c in enumerate(closes)]
    m=dict(exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',status='ok',started_at='2026-10-26T08:30:00Z',finished_at='2026-10-26T08:30:01Z',metrics={'multi_timeframe':{'data':{'4h':{'status':'ok','observed_at':'2026-10-26T08:30:00Z','data':{'interval':'4h','closed_only':True,'candles':rows}}}}})
    def cvd(start, buy, sell):
        markets={x:dict(status='ok',coverage_verified=True,market=x,coverage_scope='bitget_public_history_only',interval_start_ms=start,interval_end_ms=start+PERIOD,validated_buy_btc=str(buy),validated_sell_btc=str(sell),validated_delta_btc=str(buy-sell),value=str(buy-sell)) for x in ('spot','usdt_futures')}
        return dict(exchange='bitget',symbol='BTCUSDT',method='provider_reported_buy_minus_sell',interval_convention='[start,end)',interval_start=iso(start),interval_end=iso(start+PERIOD),status='ok',coverage_verified=True,markets=markets)
    m['cvd_4h']=cvd(end-PERIOD,8 if down else 12,12 if down else 8)
    prev=deepcopy(m);prev.update(started_at='2026-10-26T04:30:00Z',finished_at='2026-10-26T04:30:01Z',cvd_4h=cvd(end-2*PERIOD,12 if down else 8,8 if down else 12))
    return {'measurements':[m]},prev,'2026-10-26T08:31:00Z'


class MomentumTests(unittest.TestCase):
    def test_bidirectional_support_and_temporal_switch_without_probability(self):
        for down in (False,True):
            f,p,now=fixture(down);original=deepcopy(f)
            r=build(f,now,p)
            self.assertEqual(r['state'],'bearish_supported' if down else 'bullish_supported')
            self.assertEqual(r['status'],'assessed');self.assertIsNone(r['probability'])
            self.assertEqual(f,original)

    def test_missing_or_wrong_window_flow_never_full_support(self):
        for kind in ('missing','window','unverified','nan','future','candle_volume'):
            with self.subTest(kind=kind):
                f,p,now=fixture();m=f['measurements'][0];leg=m['cvd_4h']['markets']['spot']
                if kind=='missing': p=None
                elif kind=='window':leg['interval_end_ms']-=PERIOD
                elif kind=='unverified':leg['coverage_verified']=False
                elif kind=='nan':leg['value']='NaN'
                elif kind=='future':p['finished_at']='2026-10-26T09:00:00Z'
                else:m['metrics']['multi_timeframe']['data']['4h']['data']['candles'][-1]['base_volume_btc']=21
                r=build(f,now,p)
                self.assertEqual(r['status'],'partial');self.assertEqual(r['state'],'tentative_bullish_switch')
                self.assertTrue(r['missing']);self.assertIn('ONTBREEKT',render(r))

    def test_less_negative_is_not_a_bullish_switch(self):
        f,p,now=fixture();rows=f['measurements'][0]['metrics']['multi_timeframe']['data']['4h']['data']['candles']
        for row,c in zip(rows[-5:],[110,108,104,100,102]):row.update(open=c,close=c,high=c+.5,low=c-.5)
        r=build(f,now,p)
        self.assertEqual(r['state'],'bearish_weakening')

    def test_negative_futures_and_contracting_volume_are_counterevidence(self):
        f,p,now=fixture();leg=f['measurements'][0]['cvd_4h']['markets']['usdt_futures'];leg.update(validated_buy_btc='8',validated_sell_btc='12',validated_delta_btc='-4',value='-4')
        r=build(f,now,p);self.assertIn('usdt_futures',r['contradictions']);self.assertNotEqual(r['state'],'bullish_supported')
        f,p,now=fixture();leg=p['cvd_4h']['markets']['spot'];leg.update(validated_buy_btc='16',validated_sell_btc='24',validated_delta_btc='-8',value='-8')
        self.assertNotEqual(build(f,now,p)['state'],'bullish_supported')

    def test_stale_or_wrong_market_is_unavailable(self):
        f,p,now=fixture();self.assertEqual(build(f,'2026-10-26T12:31:00Z',p)['status'],'unavailable')
        f['measurements'][0]['market']='SPOT';self.assertEqual(build(f,now,p)['status'],'unavailable')

    def test_original_selection_excludes_future_observations(self):
        f,p,now=fixture()
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)/'2026/10/26';folder.mkdir(parents=True)
            (folder/'a.json').write_text(json.dumps(p))
            future=deepcopy(p);future['finished_at']='2026-10-26T10:00:00Z'
            (folder/'b.json').write_text(json.dumps(future))
            self.assertEqual(previous_record(root,f['measurements'][0]),p)

    def test_partial_combined_flow_retains_valid_spot_evidence(self):
        f,p,now=fixture();cvd=f['measurements'][0]['cvd_4h']
        cvd.update(status='partial',coverage_verified=False)
        cvd['markets']['usdt_futures'].update(status='partial',coverage_verified=False)
        r=build(f,now,p)
        self.assertIn('spot',r['groups'])
        self.assertNotIn('usdt_futures',r['groups'])
        self.assertEqual(r['status'],'partial')
        self.assertNotEqual(r['state'],'bullish_supported')

        p['cvd_4h'].update(status='partial',coverage_verified=False)
        p['cvd_4h']['markets']['usdt_futures'].update(status='partial',coverage_verified=False)
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)/'2026/10/26';folder.mkdir(parents=True)
            (folder/'partial.json').write_text(json.dumps(p))
            selected=previous_record(root,f['measurements'][0])
            self.assertIsNotNone(selected)
            self.assertIn('spot',build(f,now,selected)['groups'])
