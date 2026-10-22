import unittest
from scripts.market_outcomes import evaluate_direction

BASE = {"id": "p1", "issued_at": "2026-10-22T12:00:00+00:00",
        "horizon_hours": 4, "market": "bitget_spot_btcusdt",
        "entry_price": 80000, "direction": "bull", "model_version": "v1"}


class OutcomeTests(unittest.TestCase):
    def test_correct(self):
        result = evaluate_direction(BASE, {"observed_at": "2026-10-22T16:00:00+00:00",
                                          "market": BASE["market"], "price": 80800})
        self.assertEqual(result["verdict"], "correct")

    def test_wrong(self):
        result = evaluate_direction(BASE, {"observed_at": "2026-10-22T16:00:00+00:00",
                                          "market": BASE["market"], "price": 79000})
        self.assertEqual(result["verdict"], "incorrect")

    def test_future_or_stale_data_not_accepted(self):
        result = evaluate_direction(BASE, {"observed_at": "2026-10-22T17:00:00+00:00",
                                          "market": BASE["market"], "price": 90000})
        self.assertEqual(result["status"], "unavailable")

    def test_cross_market_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_direction(BASE, {"observed_at": "2026-10-22T16:00:00+00:00",
                                      "market": "other", "price": 90000})


if __name__ == "__main__":
    unittest.main()
