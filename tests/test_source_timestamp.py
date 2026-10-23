import re
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from scripts.enrich import collect_extra, source_timestamp


class SourceTimestampTests(unittest.TestCase):
    def test_nas_observed_nanosecond_strings_on_strict_parser(self):
        original = datetime
        class Python39Datetime(datetime):
            @classmethod
            def fromisoformat(cls, value):
                fraction = re.search(r'\.(\d+)', value)
                if fraction and len(fraction.group(1)) != 6:
                    raise ValueError('Unsupported fractional precision')
                return original.fromisoformat(value)
        with patch('scripts.enrich.datetime', Python39Datetime):
            for value, micros in [('2026-10-23T11:37:29.498846001Z', 498846),
                                  ('2026-10-23T11:37:55.303959024Z', 303959)]:
                expected = datetime(2026, 10, 23, 11, 37, 29 if micros == 498846 else 55, micros, tzinfo=timezone.utc)
                self.assertEqual(source_timestamp(value), expected.timestamp())

    def test_z_offsets_and_fraction_lengths_agree(self):
        for fraction in ('', '.1', '.123', '.123456', '.123456789'):
            with self.subTest(fraction=fraction):
                utc = source_timestamp('2026-10-23T11:37:29' + fraction + 'Z')
                offset = source_timestamp('2026-10-23T13:37:29' + fraction + '+02:00')
                self.assertEqual(utc, offset)

    def test_invalid_and_naive_times_rejected(self):
        for value in ('2026-10-23T11:37:29', '2026-10-23', '2026-13-23T11:37:29Z',
                      '2026-10-23T11:37:29.1234567890Z', 'garbage'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source_timestamp(value)

    def test_derived_metrics_keep_freshness_and_skew_validation(self):
        fixed = datetime(2026, 10, 23, 11, 38, tzinfo=timezone.utc)
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed
        for stamp, expected in [('2026-10-23T11:37:29.498846001Z', 'ok'),
                                ('2026-10-23T11:30:00.498846001Z', 'missing_data'),
                                ('2026-10-23T11:35:00.000000001Z', 'missing_data')]:
            def request(url, transform, bitget=False):
                if '/BTC-USD/' in url or '/USDT-USD/' in url:
                    data = {'price_usd': 81000 if '/BTC-USD/' in url else 1, 'source_time': stamp}
                elif 'USDCUSDT' in url:
                    data = {'price_usdt': 1, 'source_ts_ms': int(fixed.timestamp() * 1000)}
                else:
                    data = {'price_usdt': 81000, 'source_ts_ms': int(fixed.timestamp() * 1000)}
                return {'status': 'ok', 'data': data}
            with self.subTest(stamp=stamp), patch('scripts.enrich.datetime', Clock), patch('scripts.enrich.request', request):
                result = collect_extra({'futures_price': {'status': 'error', 'data': None}})
                self.assertEqual(result['stablecoins']['data']['USDC']['status'], expected)
                self.assertEqual(result['coinbase_premium_proxy']['status'], expected)
                if expected != 'ok':
                    self.assertIsNone(result['coinbase_premium_proxy']['data'])
