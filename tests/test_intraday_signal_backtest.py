from copy import deepcopy
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
from scripts import intraday_signal_backtest as b
from scripts.market_scenarios import time_ms


def candles(tf,n=240):
 p=b.history.PERIOD_MS[tf];start=time_ms('2026-01-01T00:00:00Z')
 return [dict(open_time_ms=start+i*p,open=100+i,high=101+i,low=99+i,close=100+i,base_volume_btc=10,quote_volume_usdt=1000) for i in range(n)]

class Tests(unittest.TestCase):
 def test_nonoverlap_and_horizon(self):
  for tf in ('1h','4h'):
   r=b.evaluate(candles(tf),tf,24)
   self.assertEqual(sum(x['count'] for x in r['groups']),sum(x['count'] for x in r['baseline']))
   self.assertGreater(sum(x['count'] for x in r['baseline']),1)
 def test_gap_excludes_crossing_windows(self):
  rows=candles('1h');a=b.evaluate(rows,'1h',24);q=b.evaluate(rows[:80]+rows[81:],'1h',24)
  self.assertLess(sum(x['count'] for x in q['baseline']),sum(x['count'] for x in a['baseline']))
 def test_future_changes_do_not_modify_previous_label(self):
  rows=candles('4h');old=b.model.assess(rows[:24],'4h',b.iso(rows[23]['open_time_ms']+b.history.PERIOD_MS['4h']))
  new=deepcopy(rows);new[24]['close']=1
  self.assertEqual(old,b.model.assess(new[:24],'4h',b.iso(new[23]['open_time_ms']+b.history.PERIOD_MS['4h'])))
 def test_reject_invalid_horizon_or_tf(self):
  for tf,hours in [('1h',1),('1d',24)]:
   with self.assertRaises(ValueError):b.evaluate(candles('1h'),tf,hours)
 def test_source_conflict_is_blocked(self):
  with TemporaryDirectory() as root:
   for tf in ('1h','4h'):
    p=b.history.filename(Path(root)/b.history.DIRECTORY,tf);p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
   state={'4h':{'status':'conflict','cross_timeframe_check':{'mismatch_candles':1}},'1h':{'status':'complete'}}
   with patch.object(b.history,'read',return_value=state):
    with self.assertRaisesRegex(ValueError,'source_conflict'):b.run(root,'2026-10-28T00:00:00Z')
