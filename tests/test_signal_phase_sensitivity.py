import unittest
from scripts import signal_phase_sensitivity as phase
from tests.test_intraday_signal_backtest import candles

class Tests(unittest.TestCase):
 def test_wilson_limits(self):
  lo,hi=phase.wilson(50,100);self.assertAlmostEqual(lo,.4038,places=3);self.assertAlmostEqual(hi,.5962,places=3)
  self.assertIsNone(phase.wilson(0,0))
 def test_phases_and_small_group_suppression(self):
  r=phase.phases(candles('4h',500),'4h',24,10)
  self.assertEqual(r['phase_count'],6)
  self.assertTrue(all(x['positive_rate'] is None and x['wilson_iid_approx'] is None for x in r['phases'] if x['count']<10))
  self.assertTrue(all(0<=x['phase']<6 for x in r['phases']))
 def test_gap_excludes_crossing_periods(self):
  rows=candles('1h',500);a=phase.phases(rows,'1h',24);b=phase.phases(rows[:120]+rows[121:],'1h',24)
  self.assertLess(sum(x['count'] for x in b['phases']),sum(x['count'] for x in a['phases']))
 def test_invalid_inputs_rejected(self):
  for tf,h in [('1h',1),('1d',24)]:
   with self.assertRaises(ValueError):phase.phases([],tf,h)
