import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scripts.archive_fresh_4h import run


class FreshArchiveTests(unittest.TestCase):
    def test_rejects_stale_snapshot_before_assessment(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "latest.json"
            now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
            source.write_text(json.dumps({"updated_at": (now - timedelta(hours=6)).isoformat()}))
            result = run(source, Path(folder) / "archive.jsonl", now)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "stale snapshot")

    def test_rejects_future_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "latest.json"
            now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
            source.write_text(json.dumps({"updated_at": (now + timedelta(hours=1)).isoformat()}))
            result = run(source, Path(folder) / "archive.jsonl", now)
            self.assertEqual(result["reason"], "invalid timestamp")


if __name__ == "__main__":
    unittest.main()
