import unittest
from scripts.macro_events import MacroEvent
from scripts.price_levels import retracements


class MacroAndFibTests(unittest.TestCase):
    def test_surprise(self):
        event = MacroEvent("cpi-1", "CPI", "2026-10-22T12:00:00Z",
                           "https://example.org/release", "2026-10-22T12:01:00Z",
                           actual=2.5, consensus=2.3,
                           consensus_source_url="https://example.org/consensus",
                           released_at="2026-10-22T12:00:00Z", unit="pct")
        self.assertEqual(event.as_of("2026-10-22T12:02:00Z")["direction"], "above")
        self.assertEqual(event.as_of("2026-10-22T11:00:00Z")["status"], "unavailable")

    def test_consensus_requires_source(self):
        event = MacroEvent("x", "NFP", "2026-10-22T12:00:00Z",
                           "https://example.org", "2026-10-22T12:00:00Z",
                           consensus=1)
        with self.assertRaises(ValueError):
            event.validate()

    def test_fib_log_differs_from_linear(self):
        log_levels = retracements(100, 400, method="log", ratios=[0.5])
        linear = retracements(100, 400, method="linear", ratios=[0.5])
        self.assertAlmostEqual(log_levels["levels"][0]["price"], 200)
        self.assertAlmostEqual(linear["levels"][0]["price"], 250)

    def test_invalid_anchors(self):
        with self.assertRaises(ValueError):
            retracements(0, 100)


if __name__ == "__main__":
    unittest.main()
