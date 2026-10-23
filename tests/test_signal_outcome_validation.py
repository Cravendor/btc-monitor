import unittest
from scripts.signal_outcome_validation import evaluate, evaluate_horizons


def row(time, value, grade="bullish", model="v1", tf="5m"):
    return {"model_version": model, "signals": {tf: {
        "status": "ok", "grade": grade, "model_version": model,
        "candle_closed_at": time, "close_price": value}}}


class OutcomeValidationTests(unittest.TestCase):
    def test_deduplicates_repeated_closed_candles(self):
        rows = [row("2026-10-20T00:00:00+00:00", 100)] * 3
        rows.append(row("2026-10-21T00:00:00+00:00", 110, "neutral"))
        # neutral still provides a forward price
        result = evaluate(rows)
        self.assertEqual(result["5m"]["evaluated"], 1)
        self.assertEqual(result["5m"]["confirmed_direction"], 1)

    def test_missing_forward_price_is_pending(self):
        result = evaluate([row("2026-10-20T00:00:00+00:00", 100)])
        self.assertEqual(result["5m"]["pending_forward_price"], 1)

    def test_opposite_direction_and_conflict(self):
        rows = [row("2026-10-20T00:00:00+00:00", 100, "bearish"),
                row("2026-10-21T00:00:00+00:00", 110, "neutral")]
        self.assertEqual(evaluate(rows)["5m"]["opposite_direction"], 1)
        rows.append(row("2026-10-20T00:00:00+00:00", 101, "bearish"))
        self.assertEqual(evaluate(rows)["5m"]["excluded"], 1)

    def test_multi_horizon_and_grade_separation(self):
        rows = [row("2026-10-20T00:00:00+00:00", 100, "bullish"),
                row("2026-10-20T01:00:00+00:00", 105, "neutral"),
                row("2026-10-20T04:00:00+00:00", 95, "neutral"),
                row("2026-10-21T00:00:00+00:00", 110, "neutral"),
                row("2026-10-27T00:00:00+00:00", 90, "neutral")]
        result = evaluate_horizons(rows)
        self.assertEqual(result[1]["5m"]["bullish"]["confirmed_direction"], 1)
        self.assertEqual(result[4]["5m"]["bullish"]["opposite_direction"], 1)
        self.assertEqual(result[24]["5m"]["bullish"]["confirmed_direction"], 1)
        self.assertEqual(result[168]["5m"]["bullish"]["opposite_direction"], 1)
        self.assertEqual(result[1]["5m"]["bearish"]["evaluated"], 0)

    def test_no_early_forward_prices(self):
        rows = [row("2026-10-20T00:00:00+00:00", 100),
                row("2026-10-20T23:59:00+00:00", 110, "neutral")]
        self.assertEqual(evaluate(rows)["5m"]["pending_forward_price"], 1)


if __name__ == "__main__":
    unittest.main()
