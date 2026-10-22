import json
import tempfile
import unittest
from pathlib import Path
from scripts.macro_archive import archive_source_snapshot


class ArchiveTests(unittest.TestCase):
    def test_deduplicated(self):
        record = {"source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                  "retrieved_at": "2026-10-22T12:00:00Z",
                  "status": "parsed_unconfirmed", "events": []}
        with tempfile.TemporaryDirectory() as directory:
            first = archive_source_snapshot(record, directory)
            second = archive_source_snapshot(record, directory)
            self.assertEqual(first, second)
            self.assertEqual(len(list(Path(directory).rglob("*.json"))), 1)
            self.assertEqual(json.loads(Path(first).read_text())["events"], [])

    def test_unverified_only(self):
        record = {"source_url": "https://example.org",
                  "retrieved_at": "2026-10-22T12:00:00Z",
                  "status": "parsed_unconfirmed",
                  "events": [{"verification": "verified"}]}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                archive_source_snapshot(record, directory)


if __name__ == "__main__":
    unittest.main()
