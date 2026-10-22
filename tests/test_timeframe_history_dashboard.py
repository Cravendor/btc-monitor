import tempfile
import unittest
from pathlib import Path
from scripts.timeframe_history_dashboard import render, build


class HistoryDashboardTests(unittest.TestCase):
    def test_missing_and_escaping(self):
        page = render([{"updated_at": "<bad>", "signals": {
            "5m": {"grade": "bullish", "status": "ok"},
            "1h": {"grade": "bearish", "status": "error"}}}])
        self.assertIn("&lt;bad&gt;", page)
        self.assertIn("Bullish", page)
        self.assertIn("ONTBREEKT", page)
        self.assertNotIn("<bad>", page)

    def test_empty_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "page.html"
            build(Path(directory) / "missing.jsonl", out)
            self.assertIn("Nog geen geldige", out.read_text())
