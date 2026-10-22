import json
import tempfile
import unittest
from pathlib import Path
from scripts.evaluate_bitget_snapshot import evaluate_file


class SnapshotEvaluationTests(unittest.TestCase):
    def test_missing_measurements_is_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "latest.json"
            path.write_text(json.dumps({"exchange": "bitget", "market": "USDT-FUTURES",
                                        "symbol": "BTCUSDT", "measurements": []}))
            result = evaluate_file(path, "2026-10-22T12:00:00Z")
            self.assertEqual(result["status"], "unavailable")
            self.assertIsNone(result["grade"])


if __name__ == "__main__":
    unittest.main()
