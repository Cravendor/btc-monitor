import json
import tempfile
import unittest
from pathlib import Path
from scripts.signal_archive import append_signal, export_dataset


SIGNAL = {"id": "2026-10-22-4h-example", "issued_at": "2026-10-22T12:00:00Z",
          "market": "bitget_btcusdt", "timeframe": "4h", "grade": "neutral",
          "model_version": "v1", "source": "test fixture", "quality": "verified"}


class SignalArchiveTests(unittest.TestCase):
    def test_idempotent_append_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "history.jsonl"
            output = Path(directory) / "signals.json"
            self.assertTrue(append_signal(SIGNAL, archive))
            self.assertFalse(append_signal(SIGNAL, archive))
            self.assertEqual(export_dataset(archive, output), 1)
            rows = json.loads(output.read_text())
            self.assertEqual(rows[0]["outcome"]["status"], "unavailable")

    def test_reject_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                append_signal(dict(SIGNAL, quality="partial"),
                              Path(directory) / "history.jsonl")


if __name__ == "__main__":
    unittest.main()
