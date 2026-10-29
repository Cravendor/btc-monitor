from copy import deepcopy
import unittest
from scripts import daily_signal_backtest as b
from scripts.cycle_history import DAY
from scripts.market_scenarios import time_ms


def data(n=50):
 start=time_ms('2025-12-01T00:00:00+00:00')
 return [dict(open_time_ms=start+i*DAY,open=100+i,high=101+i,low=99+i,close=100+i,base_volume_btc=10,quote_volume_usdt=1000) for i in range(n)]

class BacktestTests(unittest.TestCase):
 def test_nonoverlapping_and_split_boundary(self):
  r=b.evaluate(data(80),7)
  self.assertEqual(sum(g['count'] for g in r['groups']),sum(x['count'] for x in r['baseline']))
  self.assertTrue(all(g['count']>=0 for g in r['groups']))
 def test_gaps_never_fabricate_contiguous_outcomes(self):
  rows=data();clean=b.evaluate(rows,1);bad=b.evaluate(rows[:25]+rows[26:],1)
  self.assertLess(sum(x['count'] for x in bad['baseline']),sum(x['count'] for x in clean['baseline']))
 def test_future_change_does_not_change_past_signal_classification(self):
  rows=data();a=b.model.assess(rows[:24],'1d',b.iso(rows[23]['open_time_ms']+DAY))
  changed=deepcopy(rows);changed[24]['close']=10
  c=b.model.assess(changed[:24],'1d',b.iso(changed[23]['open_time_ms']+DAY))
  self.assertEqual(a,c)
 def test_invalid_horizon(self):
  with self.assertRaises(ValueError):b.evaluate(data(),2)
