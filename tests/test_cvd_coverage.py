"""Fail-closed CVD interval coverage tests."""
import unittest
from datetime import datetime, timezone
from scripts.cvd_coverage import validate_coverage, INTERVAL_MS

START = (int(datetime(2026, 10, 20, tzinfo=timezone.utc).timestamp()*1000) // INTERVAL_MS)*INTERVAL_MS
END = START + INTERVAL_MS
TRADES = [{'id': 'a', 'ts_ms': START+1000, 'size_btc': 2, 'side': 'buy'},
          {'id': 'b', 'ts_ms': START+2000, 'size_btc': 1, 'side': 'sell'}]
FLAGS = dict(source_complete=True, gaps_checked=True, pagination_complete=True)


class TestCvdCoverage(unittest.TestCase):
    def test_no_attestation(self):
        self.assertEqual(validate_coverage(TRADES, START, END)['status'], 'incomplete')

    def test_complete(self):
        result = validate_coverage(TRADES, START, END, **FLAGS)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['value'], 1)

    def test_duplicate(self):
        self.assertEqual(validate_coverage(TRADES + [TRADES[0]], START, END, **FLAGS)['status'], 'incomplete')

    def test_out_of_window(self):
        bad = [dict(TRADES[0], ts_ms=END)]
        self.assertEqual(validate_coverage(bad, START, END, **FLAGS)['status'], 'incomplete')

    def test_missing_side(self):
        bad = [dict(TRADES[0], side='unknown')]
        self.assertEqual(validate_coverage(bad, START, END, **FLAGS)['status'], 'incomplete')

    def test_wrong_window(self):
        self.assertEqual(validate_coverage(TRADES, START+1, END+1, **FLAGS)['status'], 'incomplete')
