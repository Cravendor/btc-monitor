import unittest
from scripts.fomc_calendar_source import source_snapshot


class FomcSourceTests(unittest.TestCase):
    def test_source_not_fabricated_events(self):
        snapshot = source_snapshot("<html><body>FOMC calendar</body></html>",
                                   "2026-10-22T12:00:00+00:00")
        self.assertEqual(snapshot["events"], [])
        self.assertEqual(snapshot["status"], "parsed_unconfirmed")

    def test_unexpected_page_rejected(self):
        with self.assertRaises(ValueError):
            source_snapshot("<html>Access denied</html>")


if __name__ == "__main__":
    unittest.main()
