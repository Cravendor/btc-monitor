import unittest
from scripts.context_comparison import compare_context

def record(grade, at):
    return {"status":"provisional","grade":grade,"observed_at":at,
            "source":"Bitget USDT-FUTURES BTCUSDT latest.json"}

class ComparisonTests(unittest.TestCase):
    def test_bullish_shift(self):
        a=record("neutral","2026-10-22T04:00:00Z")
        b=record("slightly_bullish","2026-10-22T08:00:00Z")
        result=compare_context(b,a)
        self.assertEqual(result["trend"],"more_bullish")
        self.assertEqual(result["grade_step_change"],1)
    def test_same_candle_rejected(self):
        a=record("neutral","2026-10-22T04:00:00Z")
        self.assertEqual(compare_context(a,a)["status"],"unavailable")
    def test_missing_rejected(self):
        a=record("neutral","2026-10-22T04:00:00Z")
        self.assertEqual(compare_context({"status":"unavailable"},a)["status"],"unavailable")

if __name__=="__main__":
    unittest.main()
