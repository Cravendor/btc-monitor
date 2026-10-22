import unittest
from datetime import datetime, timedelta, timezone
from scripts.context_trends import trend_windows

NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


def row(at, grade):
    return {"observed_at": at.isoformat(), "grade": grade,
            "quality": "provisional_price_only",
            "source": "Bitget USDT-FUTURES BTCUSDT latest.json",
            "model_version": "price_trend_4h_v0.1"}


class TrendTests(unittest.TestCase):
    def test_one_record_does_not_invent_trends(self):
        result = trend_windows([row(NOW, "neutral")], NOW.isoformat())
        self.assertTrue(all(x["status"] == "unavailable" for x in result["windows"].values()))

    def test_24h_change_and_missing_long_windows(self):
        result = trend_windows([row(NOW - timedelta(hours=24), "bearish"),
                                row(NOW, "neutral")], NOW.isoformat())
        self.assertEqual(result["windows"]["24h"]["grade_step_change"], 2)
        self.assertEqual(result["windows"]["7d"]["status"], "unavailable")

    def test_future_data_not_used(self):
        result = trend_windows([row(NOW + timedelta(hours=4), "bullish")], NOW.isoformat())
        self.assertEqual(result["status"], "unavailable")

    def test_stale_latest_rejected(self):
        result = trend_windows([row(NOW - timedelta(days=2), "neutral")], NOW.isoformat())
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
