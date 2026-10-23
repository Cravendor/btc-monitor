import unittest
from scripts.signal_statistics import wilson_interval, descriptive_confidence
from scripts.timeframe_history_dashboard import outcome_html


class SignalStatisticsTests(unittest.TestCase):
    def test_wilson_known_values(self):
        low, high = wilson_interval(50, 100)
        self.assertAlmostEqual(low, 0.4038, places=3)
        self.assertAlmostEqual(high, 0.5962, places=3)

    def test_extreme_values_and_invalid(self):
        low, high = wilson_interval(0, 30)
        self.assertEqual(low, 0)
        self.assertGreater(high, 0)
        self.assertIsNone(wilson_interval(0, 0))
        self.assertIsNone(wilson_interval(5, 4))
        self.assertIsNone(wilson_interval(True, 10))

    def test_sample_threshold(self):
        self.assertEqual(descriptive_confidence(20, 29)["status"], "insufficient")
        self.assertIsNone(descriptive_confidence(20, 29)["interval"])
        self.assertEqual(descriptive_confidence(20, 30)["status"], "descriptive_only")

    def test_dashboard_explains_limitations(self):
        page = outcome_html([])
        self.assertIn("95%-interval", page)
        self.assertIn("autocorrelatie", page)
        self.assertIn("ONVOLDOENDE DATA", page)


if __name__ == "__main__":
    unittest.main()
