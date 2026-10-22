import tempfile
import unittest
from pathlib import Path
from scripts.provisional_context_archive import append_context

RECORD = {"status": "provisional", "grade": "neutral", "confidence": "low",
          "source": "Bitget USDT-FUTURES BTCUSDT latest.json",
          "observed_at": "2026-10-22T04:00:00Z",
          "derivatives_observed_at": "2026-10-22T04:52:40Z",
          "cvd_status": "unavailable", "price_score": 0}


class ArchiveTests(unittest.TestCase):
    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.jsonl"
            self.assertTrue(append_context(RECORD, path))
            self.assertFalse(append_context(RECORD, path))
            self.assertEqual(len(path.read_text().splitlines()), 1)

    def test_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.jsonl"
            append_context(RECORD, path)
            with self.assertRaises(ValueError):
                append_context(dict(RECORD, grade="bearish"), path)

    def test_unconfirmed_is_not_verified_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                append_context(dict(RECORD, confidence="high"),
                               Path(directory) / "context.jsonl")


if __name__ == "__main__":
    unittest.main()
