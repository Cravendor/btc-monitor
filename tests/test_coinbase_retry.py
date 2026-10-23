import io
import json
import ssl
import unittest
from datetime import datetime, timedelta, timezone
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts.enrich import collect_extra, request, stable

USDT = 'https://api.exchange.coinbase.com/products/USDT-USD/ticker'
BTC = 'https://api.exchange.coinbase.com/products/BTC-USD/ticker'


def response(price='1', stamp=None):
    return io.StringIO(json.dumps({'price': price,
                                  'time': stamp or datetime.now(timezone.utc).isoformat()}))


class CoinbaseRetryTests(unittest.TestCase):
    def test_read_timeout_then_success_is_fresh_and_has_no_stale_error(self):
        observed = []
        def transform(data):
            observed.append(data)
            return stable(data)
        first = datetime(2026, 10, 23, 16, 30, tzinfo=timezone.utc)
        class Clock(datetime):
            ticks = iter((first, first + timedelta(seconds=16)))
            @classmethod
            def now(cls, tz=None):
                return next(cls.ticks)
        with patch('scripts.enrich.datetime', Clock), \
                patch('scripts.enrich.urlopen', side_effect=[TimeoutError('read timeout'), response()]) as open_, \
                patch('scripts.enrich.time.sleep') as sleep:
            result = request(USDT, transform)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(result['observed_at'], (first+timedelta(seconds=16)).isoformat())
        self.assertEqual(result['data']['price_usd'], 1)
        self.assertNotIn('error', result)
        self.assertEqual(len(observed), 1)
        self.assertEqual(open_.call_count, 2)
        self.assertEqual([c.kwargs['timeout'] for c in open_.call_args_list], [15, 15])
        sleep.assert_called_once_with(1)

    def test_timeouts_stop_after_three_attempts_with_no_cached_value(self):
        with patch('scripts.enrich.urlopen', side_effect=TimeoutError('read timeout')) as open_, \
                patch('scripts.enrich.time.sleep') as sleep:
            result = request(USDT, stable)
        self.assertEqual(open_.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['attempts'], 3)
        self.assertIsNone(result['data'])

    def test_python39_socket_timeout_does_not_need_to_inherit_timeout_error(self):
        class LegacySocketTimeout(OSError):
            pass
        with patch('scripts.enrich.socket.timeout', LegacySocketTimeout), \
                patch('scripts.enrich.urlopen', side_effect=[LegacySocketTimeout('read timeout'), response()]) as open_, \
                patch('scripts.enrich.time.sleep'):
            result = request(USDT, stable)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(open_.call_count, 2)

    def test_retryable_http_codes_and_transport_failures(self):
        errors = [HTTPError(USDT, code, 'temporary', {}, None) for code in (500, 502, 503, 504)]
        errors.extend((URLError(TimeoutError('timeout')), ConnectionResetError('reset'),
                       IncompleteRead(b'partial', 100)))
        for error in errors:
            with self.subTest(error=error), \
                    patch('scripts.enrich.urlopen', side_effect=[error, response()]) as open_, \
                    patch('scripts.enrich.time.sleep') as sleep:
                result = request(USDT, stable)
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(open_.call_count, 2)
                sleep.assert_called_once_with(1)

    def test_rate_limit_access_restrictions_and_other_http_errors_are_not_retried(self):
        for code in (400, 401, 403, 404, 408, 429, 451, 501):
            with self.subTest(code=code), \
                    patch('scripts.enrich.urlopen', side_effect=HTTPError(USDT, code, 'refused', {}, None)) as open_, \
                    patch('scripts.enrich.time.sleep') as sleep:
                result = request(USDT, stable)
                self.assertEqual(result['status'], 'error')
                self.assertIsNone(result['data'])
                self.assertEqual(open_.call_count, 1)
                sleep.assert_not_called()

    def test_certificate_validation_errors_are_not_retried(self):
        for error in (ssl.SSLCertVerificationError('invalid certificate'),
                      URLError(ssl.SSLCertVerificationError('invalid certificate'))):
            with self.subTest(error=error), patch('scripts.enrich.urlopen', side_effect=error) as open_, \
                    patch('scripts.enrich.time.sleep') as sleep:
                result = request(USDT, stable)
                self.assertEqual(result['status'], 'error')
                self.assertEqual(open_.call_count, 1)
                sleep.assert_not_called()

    def test_malformed_json_invalid_prices_and_missing_fields_do_not_retry(self):
        for payload in ('invalid JSON', '{}', '{"price":"NaN"}', '{"price":"-1"}', '{"price":"1"}'):
            with self.subTest(payload=payload), \
                    patch('scripts.enrich.urlopen', return_value=io.StringIO(payload)) as open_, \
                    patch('scripts.enrich.time.sleep') as sleep:
                result = request(USDT, stable)
                self.assertEqual(result['status'], 'error')
                self.assertIsNone(result['data'])
                self.assertEqual(open_.call_count, 1)
                sleep.assert_not_called()

    def test_validation_timeout_is_not_treated_as_transport_timeout(self):
        def invalid(_):
            raise TimeoutError('transform failed')
        with patch('scripts.enrich.urlopen', return_value=response()) as open_, \
                patch('scripts.enrich.time.sleep') as sleep:
            result = request(USDT, invalid)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(open_.call_count, 1)
        sleep.assert_not_called()

    def test_retries_are_limited_to_exact_existing_coinbase_ticker_urls(self):
        for url, expected in ((USDT, 3), (BTC, 3),
                              ('https://api.bitget.com/api/v2/spot/market/tickers', 1),
                              (USDT+'?other=1', 1),
                              (USDT.replace('https:', 'http:'), 1),
                              (USDT.replace('coinbase.com/', 'coinbase.com.invalid/'), 1)):
            with self.subTest(url=url), patch('scripts.enrich.urlopen', side_effect=TimeoutError()) as open_, \
                    patch('scripts.enrich.time.sleep'):
                result = request(url, stable)
                self.assertEqual(result['attempts'], expected)
                self.assertEqual(open_.call_count, expected)

    def test_response_and_http_error_body_are_closed(self):
        body = io.StringIO('temporary')
        error = HTTPError(USDT, 503, 'temporary', {}, body)
        good = response()
        with patch('scripts.enrich.urlopen', side_effect=[error, good]), patch('scripts.enrich.time.sleep'):
            result = request(USDT, stable)
        self.assertEqual(result['status'], 'ok')
        self.assertTrue(body.closed)
        self.assertTrue(good.closed)

    def test_bodyless_http_error_does_not_call_broken_python39_close(self):
        class LegacyBodylessError(HTTPError):
            def __init__(self, *args):
                super().__init__(*args)
                # Newer Python inserts an empty BytesIO; 3.9.14 leaves fp None.
                self.fp = None
            def close(self):
                raise KeyError('file')
        for code, expected_calls in ((403, 1), (429, 1), (451, 1), (503, 2)):
            error = LegacyBodylessError(USDT, code, 'test', {}, None)
            with self.subTest(code=code), \
                    patch('scripts.enrich.urlopen', side_effect=[error, response()]) as open_, \
                    patch('scripts.enrich.time.sleep'):
                result = request(USDT, stable)
                self.assertEqual(open_.call_count, expected_calls)
                self.assertEqual(result['status'], 'ok' if code == 503 else 'error')
                if code != 503:
                    self.assertIsNone(result['data'])


class CoinbaseDependenciesTests(unittest.TestCase):
    def collect(self, stamp, fail_usdt=False):
        fixed = datetime(2026, 10, 23, 16, 30, tzinfo=timezone.utc)
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed
        usdt_calls = []
        def open_(req, timeout):
            url = req.full_url
            if url == USDT:
                usdt_calls.append(url)
                if len(usdt_calls) == 1 or fail_usdt:
                    raise TimeoutError('read timeout')
                return response(stamp=stamp)
            if url == BTC:
                return response(price='81000', stamp=stamp)
            if 'spot/market/tickers' in url:
                symbol = 'USDCUSDT' if 'USDCUSDT' in url else 'BTCUSDT'
                price = '1' if symbol == 'USDCUSDT' else '81000'
                return io.StringIO(json.dumps({'code': '00000', 'data': [
                    {'symbol': symbol, 'lastPr': price, 'ts': str(int(fixed.timestamp()*1000))}]}))
            return io.StringIO('{"code":"error"}')
        with patch('scripts.enrich.datetime', Clock), patch('scripts.enrich.urlopen', side_effect=open_), \
                patch('scripts.enrich.time.sleep'):
            result = collect_extra({'futures_price': {'status': 'error', 'data': None}})
        return result, len(usdt_calls)

    def test_successful_retry_restores_both_dependencies_from_one_shared_request(self):
        result, calls = self.collect('2026-10-23T16:29:59.123456789Z')
        self.assertEqual(calls, 2)
        self.assertEqual(result['stablecoins']['status'], 'ok')
        self.assertEqual(result['coinbase_premium_proxy']['status'], 'ok')
        self.assertEqual(result['stablecoins']['data']['USDT']['attempts'], 2)
        self.assertIs(result['coinbase_premium_proxy']['sources']['usdt'],
                      result['stablecoins']['data']['USDT'])

    def test_exhausted_retries_keep_partial_and_missing_dependencies(self):
        result, calls = self.collect('2026-10-23T16:29:59Z', fail_usdt=True)
        self.assertEqual(calls, 3)
        self.assertEqual(result['stablecoins']['status'], 'partial')
        self.assertEqual(result['coinbase_premium_proxy']['status'], 'missing_data')
        self.assertIsNone(result['coinbase_premium_proxy']['data'])
        self.assertIsNone(result['stablecoins']['data']['USDC']['data'])

    def test_retried_old_or_skewed_sources_still_cannot_produce_derived_values(self):
        for stamp in ('2026-10-23T16:20:00Z', '2026-10-23T16:27:59Z'):
            with self.subTest(stamp=stamp):
                result, calls = self.collect(stamp)
                self.assertEqual(calls, 2)
                self.assertEqual(result['coinbase_premium_proxy']['status'], 'missing_data')
                self.assertIsNone(result['coinbase_premium_proxy']['data'])
                self.assertEqual(result['stablecoins']['data']['USDC']['status'], 'missing_data')
