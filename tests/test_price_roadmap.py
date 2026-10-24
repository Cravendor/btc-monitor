from copy import deepcopy
from datetime import datetime, timezone
import io
from http.client import IncompleteRead
import unittest

from scripts.ath_reference import MAX_BYTES, fetch_reference, validate
from scripts.market_scenarios import STEP, iso
from scripts.price_roadmap import build_roadmap, change_pct
from scripts.roadmap_dashboard import render


def fixture():
    now = datetime(2026, 10, 24, 5, 30, tzinfo=timezone.utc)
    ms = int(now.timestamp()*1000)
    native = {}
    for tf, period in (('4h',STEP),('1d',86400000),('1w',604800000)):
        offset = 4*86400000 if tf == '1w' else 0
        boundary = (ms-offset)//period*period+offset
        rows = []
        for i in range(24):
            high = 120-i*.5
            low = 100-i*.5
            rows.append({'open_time_ms':boundary-(24-i)*period,'open':high-5,'high':high,
                         'low':low,'close':high-5,'base_volume_btc':10,'quote_volume_usdt':1000})
        native[tf] = {'status':'ok','observed_at':now.isoformat(),
                      'data':{'interval':tf,'closed_only':True,'candles':rows}}
    ticker = {'status':'ok','data':{'lastPr':'98','ts':str(ms)}}
    feed = {'measurements':[{'exchange':'bitget','market':'USDT-FUTURES','symbol':'BTCUSDT',
                            'started_at':now.isoformat(),'finished_at':now.isoformat(),
                            'metrics':{'candles_4h':deepcopy(native['4h']),
                                       'futures_price':ticker,'multi_timeframe':{'data':native}}}]}
    feed['measurements'][0]['metrics']['candles_4h']['data']['interval'] = '4H'
    return feed, now.isoformat()


class RoadmapTests(unittest.TestCase):
    def test_routes_keep_three_timeframes_and_percentage_bases_separate(self):
        feed, now = fixture()
        r = build_roadmap(feed, now)
        self.assertEqual([x['timeframe'] for x in r['horizons']], ['4h','1d','1w'])
        for horizon in r['horizons']:
            self.assertEqual(horizon['status'], 'ready')
            self.assertFalse(horizon['bull_cycle_confirmed'])
            self.assertIsNone(horizon['ath'])
            prices = [x['price'] for x in horizon['upward']]
            self.assertEqual(prices, sorted(set(prices)))
            for level in horizon['upward']:
                self.assertGreater(level['price'], 98)
                self.assertAlmostEqual(level['distance_pct'], (level['price']/98-1)*100)
                for target in level['rejection_to']:
                    self.assertLess(target['price'], level['price'])
                    self.assertAlmostEqual(target['change_pct'], (target['price']/level['price']-1)*100)
        self.assertAlmostEqual(change_pct(100,80), -20)
        self.assertAlmostEqual(change_pct(80,100), 25)

    def test_missing_daily_does_not_relabel_short_term_as_macro(self):
        feed, now = fixture()
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['status']='error'
        r = build_roadmap(feed, now)
        self.assertEqual(r['horizons'][1]['status'], 'unavailable')
        self.assertEqual(r['horizons'][2]['status'], 'ready')
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1w']['data']['candles'].pop()
        self.assertEqual(build_roadmap(feed,now)['horizons'][2]['status'], 'unavailable')

    def test_stale_or_missing_price_never_generates_current_distances(self):
        feed, now = fixture()
        feed['measurements'][0]['metrics']['futures_price']['status']='error'
        self.assertEqual(build_roadmap(feed,now)['status'],'unavailable')
        self.assertEqual(build_roadmap(fixture()[0],'2026-10-24T08:00:00Z')['status'],'unavailable')

    def test_render_labels_rejection_math_and_unavailable_ath(self):
        feed, now = fixture()
        page = render(build_roadmap(feed,now))
        for text in ('vanaf de geteste zone','Afstand','ATH-referentie ONTBREEKT',
                     'geen bewezen all-time high','geen voorspelde bodem'):
            if text != 'Afstand': self.assertIn(text,page)
        self.assertIn('low', page.lower())


class AthReferenceTests(unittest.TestCase):
    def payload(self):
        return {'id':'bitcoin','symbol':'btc','market_data':{'current_price':{'usd':80},
                'ath':{'usd':100},'ath_date':{'usd':'2025-01-01T00:00:00Z'},
                'last_updated':'2026-10-24T05:00:00Z'}}

    def test_ath_distance_uses_same_provider_currency_and_correct_denominator(self):
        r=validate(self.payload(),'2026-10-24T05:10:00Z')
        self.assertEqual(r['unit'],'USD')
        self.assertAlmostEqual(r['to_ath_pct'],25)
        self.assertAlmostEqual(r['from_ath_pct'],-20)
        self.assertEqual(r['scope'],'provider_aggregated_spot_reference')

    def test_stale_future_wrong_asset_or_inconsistent_prices_are_rejected(self):
        for key,value in (('last_updated','2026-10-24T01:00:00Z'),
                          ('last_updated','2026-10-25T00:00:00Z'),
                          ('ath_date',{'usd':'2027-01-01T00:00:00Z'}),
                          ('ath',{'usd':79}),('current_price',{'usd':'NaN'})):
            p=self.payload();p['market_data'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(p,'2026-10-24T05:10:00Z')
        p=self.payload();p['id']='other'
        with self.assertRaises(ValueError):validate(p,'2026-10-24T05:10:00Z')

    def test_request_has_one_attempt_fixed_endpoint_timeout_and_size_bound(self):
        class Opener:
            calls=0
            def open(self,req,timeout):
                self.calls+=1
                self.url=req.full_url;self.timeout=timeout
                return io.BytesIO(b'x'*(MAX_BYTES+1))
        opener=Opener()
        self.assertEqual(fetch_reference('2026-10-24T05:10:00Z',opener)['status'],'unavailable')
        self.assertEqual(opener.calls,1)
        self.assertEqual(opener.timeout,8)
        self.assertTrue(opener.url.startswith('https://api.coingecko.com/api/v3/coins/bitcoin?'))

    def test_incomplete_reference_response_does_not_break_dashboard(self):
        class Opener:
            def open(self, req, timeout): raise IncompleteRead(b'partial')
        self.assertEqual(fetch_reference('2026-10-24T05:10:00Z',Opener())['status'],'unavailable')


if __name__=='__main__':unittest.main()
