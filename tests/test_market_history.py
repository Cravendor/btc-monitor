import tempfile
import unittest
from pathlib import Path
from scripts.market_intelligence import Indicator, aggregate
from scripts.market_history import append_snapshot, read_snapshots


class HistoryTests(unittest.TestCase):
    def test_append_and_read(self):
        indicator = Indicator("spot_cvd", "4h", None, "unverified", 1,
                              "2026-10-22T12:00:00+00:00", "Bitget",
                              "Trade coverage not established")
        result = aggregate([indicator])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history" / "signals.jsonl"
            append_snapshot(path, indicators=[indicator], aggregate_result=result)
            append_snapshot(path, indicators=[indicator], aggregate_result=result)
            records = list(read_snapshots(path))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["aggregate"]["label"], "unavailable")
        self.assertEqual(records[0]["psychology"]["phase"], "undetermined")
        self.assertEqual(records[0]["indicators"][0]["quality"], "unverified")

    def test_naive_time_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                append_snapshot(Path(tmp) / "a.jsonl", indicators=[],
                                aggregate_result={"label": "unavailable"},
                                observed_at="2026-10-22T12:00:00")


if __name__ == "__main__":
    unittest.main()
