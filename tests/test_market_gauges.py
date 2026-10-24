from copy import deepcopy
import unittest
from unittest.mock import Mock
from tests.test_price_roadmap import fixture
from scripts.market_gauges import build_gauges,render,render_all,svg
from scripts.home_dashboard import render as home
from scripts.market_scenarios import time_ms,iso
from scripts.sentiment_reference import validate,fetch_reference


class GaugeTests(unittest.TestCase):
    def test_three_visible_meters_per_mode_and_no_trade_labels(self):
        feed,now=fixture()
        self.assertEqual(render(feed,now).count('<article class="meter"'),3)
        page=render_all(feed,now)
        self.assertEqual(page.count('<article class="meter"'),6)
        self.assertIn('data-mode-panel="position" hidden',page)
        self.assertIn('Niveaucheck',page)
        for text in ('BUY','SELL','HOLD','modeltrade','modelpositie'):
            self.assertNotIn(text,page)
        self.assertNotIn('class="gauge-needle"',svg(None,'missing'))
        self.assertIn('class="gauge-needle"',svg(0,'neutral'))

    def test_swing_weekly_independent_of_4h_and_each_other(self):
        feed,now=fixture()
        del feed['measurements'][0]['metrics']['candles_4h']
        self.assertIsNotNone(build_gauges(feed,now)[0]['value'])
        feed['measurements'][0]['metrics']['multi_timeframe']['data']['1d']['status']='error'
        self.assertIsNone(build_gauges(feed,now)[0]['value'])
        self.assertIsNotNone(build_gauges(feed,now,mode='position')[0]['value'])

    def test_bad_latest_and_stale_never_show_neutral_as_missing(self):
        feed,now=fixture()
        for change in ('missing','stale','wrong','gap'):
            f=deepcopy(feed);m=f['measurements'][0]
            if change=='missing':f['measurements']=[]
            if change=='stale':m['started_at']=iso(time_ms(now)-7200000)
            if change=='wrong':m['market']='SPOT'
            if change=='gap':m['metrics']['multi_timeframe']['data']['1d']['data']['candles'].pop(-3)
            self.assertIsNone(build_gauges(f,now)[0]['value'])

    def test_missing_quote_hides_level_not_momentum(self):
        feed,now=fixture()
        feed['measurements'][0]['metrics']['futures_price']['status']='error'
        items=build_gauges(feed,now)
        self.assertIsNotNone(items[0]['value'])
        self.assertIsNone(items[1]['value'])

    def test_sentiment_zero_full_scale_and_source_attribution(self):
        feed,now=fixture()
        for score in (0,100):
            ref=validate({'data':[dict(value=str(score),value_classification='source category',timestamp=str(time_ms(now)//1000))]},'Alternative.me',now)
            ref['fallback']=True
            self.assertEqual(build_gauges(feed,now,ref)[2]['value'],score/50-1)
            self.assertIn('reservebron',render(feed,now,ref))
        for value in (None,True,101,-1,'nan'):
            with self.assertRaises((TypeError,ValueError)):
                validate({'data':[dict(value=value,value_classification='x',timestamp=str(time_ms(now)//1000))]},'Alternative.me',now)

    def test_sentiment_timestamp_and_failure(self):
        _,now=fixture()
        payload={'data':dict(value=45,value_classification='Neutral',update_time=now)}
        self.assertEqual(validate(payload,'CoinMarketCap',now)['value'],45)
        for t in (iso(time_ms(now)-37*3600000),iso(time_ms(now)+7200000)):
            payload['data']['update_time']=t
            with self.assertRaises(ValueError):validate(payload,'CoinMarketCap',now)
        opener=Mock();opener.open.side_effect=OSError('offline')
        self.assertEqual(fetch_reference(now,opener)['status'],'unavailable')
        self.assertEqual(opener.open.call_count,2)

    def test_home_controls_details_and_expiry(self):
        feed,now=fixture();page=home(feed,now)
        self.assertEqual(page.count('<article class="meter"'),6)
        self.assertEqual(page.count('<summary>Uitleg en onderbouwing</summary>'),6)
        self.assertIn('setMarketMode',page)
        self.assertIn('refreshGauges()',page)
        self.assertIn('expireRoutes()',page)
        self.assertNotIn('<details open',page)
        self.assertIn("section.querySelector('.badge')",page)
        self.assertIn('niet gekalibreerd',page)
        self.assertIn('Nieuws en psychologische context',page)
