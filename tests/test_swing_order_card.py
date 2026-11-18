import unittest
from test_market_scenarios import fixture
from scripts.market_scenarios import build_scenarios
from scripts.swing_order_card import snapshot


class OrderCardTests(unittest.TestCase):
    def test_closed_breakout_retest_and_independent_target_converted_to_usd(self):
        feed, now = fixture()
        metrics = feed['measurements'][0]['metrics']
        fx = {'price_usd': 0.98, 'source_time': now}
        metrics['stablecoins'] = {'status': 'ok', 'data': {'USDT': {'status': 'ok', 'data': fx}}}
        rows = metrics['candles_4h']['data']['candles']
        rows[0]['high'] = 150
        rows[-2].update(high=120, close=118)
        rows[-1].update(open=118, high=120, low=109, close=115)
        metrics['futures_price']['data']['lastPr'] = '115'
        result = build_scenarios(feed, now)
        plan = snapshot(feed, result, now)
        self.assertEqual(plan['side'], 1)
        self.assertAlmostEqual(plan['entry'], 110 * .98)
        self.assertAlmostEqual(plan['target'], 150 * .98)
        self.assertLess(plan['stop'], 109 * .98)
        fx['source_time'] = '1970-01-01T00:00:00Z'
        self.assertNotIn('expires', snapshot(feed, result, now))
