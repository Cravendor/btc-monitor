import json
import tempfile
import unittest
from pathlib import Path
from scripts.timeframe_signal_history import record_health


class SignalPriceHistoryTests(unittest.TestCase):
    def test_valid_price_and_model_are_recorded(self):
        health = {"exchange": "bitget", "market": "USDT-FUTURES", "symbol": "BTCUSDT",
                  "updated_at": "2026-10-22T21:00:00+00:00",
                  "timeframes": {"4h": {"status": "ok", "signal_status": "provisional",
                    "grade": "slightly_bullish", "observed_at": "2026-10-22T20:00:00+00:00",
                    "candle_close_price": "84518.7", "model_version": "multi_tf_evidence_v0.2",
                    "evidence_state": "aligned"}}}
        with tempfile.TemporaryDirectory() as tmp:
            result = record_health(health, Path(tmp) / "history.jsonl")
            self.assertEqual(result["signals"]["4h"]["close_price"], 84518.7)
            self.assertEqual(result["signals"]["4h"]["evidence_state"], "aligned")
            self.assertIsNone(result["signals"]["1d"]["close_price"])

    def test_invalid_prices_remain_missing(self):
        for bad in ("NaN", "-1", "Infinity", "abc", None):
            health = {"exchange": "bitget", "market": "USDT-FUTURES", "symbol": "BTCUSDT",
                      "updated_at": "2026-10-22T21:00:00+00:00",
                      "timeframes": {"5m": {"status": "ok", "signal_status": "provisional",
                          "grade": "neutral", "candle_close_price": bad}}}
            with self.subTest(price=bad), tempfile.TemporaryDirectory() as tmp:
                row = record_health(health, Path(tmp) / "history.jsonl")
                self.assertIsNone(row["signals"]["5m"]["close_price"])
