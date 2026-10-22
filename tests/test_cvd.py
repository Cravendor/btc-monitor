import io
import json
import unittest
from scripts.cvd import collect_cvd, INTERVAL


class CvdTests(unittest.TestCase):
    def run_case(self, pages, volume=3, quote=30, **kw):
        calls = []
        def opener(req, **kwargs):
            calls.append(req.full_url)
            return io.StringIO(json.dumps({'code':'00000','data':pages.pop(0)}))
        candle = {'status':'ok','data':{'candles':[{'open_time_ms':INTERVAL,
            'base_volume_btc':volume,'quote_volume_usdt':quote}]}}
        result = collect_cvd(candle, now_ms=2*INTERVAL+1, opener=opener, sleep=lambda _:None, **kw)
        return result, calls

    def trade(self, tid, ts=INTERVAL, side='Buy', size='2'):
        return dict(tradeId=str(tid), ts=str(ts), side=side, size=size, price='10', symbol='BTCUSDT')

    def test_full_pagination_and_boundary(self):
        result, calls = self.run_case([[self.trade(3)], [self.trade(2,2*INTERVAL-1,'Sell','1')], []])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['value'],'1')
        self.assertIn('idLessThan=3',calls[1])
        self.assertEqual(result['data']['trade_count'],2)

    def test_mismatch_null(self):
        r,_=self.run_case([[self.trade(3)],[]])
        self.assertIsNone(r['value'])
        self.assertEqual(r['status'],'missing_data')

    def test_cap_null(self):
        r,_=self.run_case([[self.trade(3)]],max_pages=1)
        self.assertIsNone(r['value'])

    def test_wrong_interval_side_and_nan(self):
        for row in [self.trade(3,2*INTERVAL),self.trade(3,side='unknown'),self.trade(3,size='NaN')]:
            with self.subTest(row=row):
                r,_=self.run_case([[row],[]])
                self.assertIsNone(r['data'])

    def test_duplicate_deduplicated(self):
        row=self.trade(3)
        r,_=self.run_case([[row,row],[]],volume=2,quote=20)
        self.assertEqual(r['value'],'2')
        self.assertEqual(r['duplicates'],1)

    def test_stalled_pagination(self):
        row=self.trade(3)
        r,_=self.run_case([[row],[row]])
        self.assertIsNone(r['value'])

    def test_quote_mismatch(self):
        r,_=self.run_case([[self.trade(3)],[]],volume=2,quote=21)
        self.assertIsNone(r['value'])

    def test_missing_candle_and_timeout(self):
        self.assertIsNone(collect_cvd({'status':'error'})['value'])
        r,_=self.run_case([],budget_seconds=0)
        self.assertIsNone(r['value'])
