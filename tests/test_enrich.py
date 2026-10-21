import unittest
from datetime import datetime, timezone
from scripts.enrich import candles, depth, derived

class SupplementTests(unittest.TestCase):
    def test_closed_candles_exclude_live(self):
        t=int(datetime.now(timezone.utc).timestamp()*1000)//14400000*14400000
        data=candles([[t,100,110,90,105,3,300],[t-14400000,100,110,90,105,3,300]])
        self.assertEqual(len(data['candles']),1)
        self.assertEqual(data['candles'][0]['open_time_ms'],t-14400000)
    def test_truncated_depth_flag(self):
        data=depth({'ts':'123','bids':[['99.99','2']], 'asks':[['100.01','3']]})
        self.assertFalse(data['bands_pct']['1.0']['bid_band_covered'])
        self.assertLess(data['bands_pct']['1.0']['imbalance'],0)
    def test_dependency_failure_not_zero(self):
        data=derived({'x':{'status':'error','data':None}},lambda _: 0)
        self.assertIsNone(data['data'])
        self.assertEqual(data['status'],'missing_data')
    def test_crossed_depth_rejected(self):
        with self.assertRaises(ValueError):
            depth({'ts':'123','bids':[['101','1']],'asks':[['100','1']]})
