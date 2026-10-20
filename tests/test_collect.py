import io
import json
import unittest
from urllib.error import HTTPError, URLError
from scripts.collect import fetch


class FetchTests(unittest.TestCase):
    def response(self, payload):
        return lambda *a, **kw: io.StringIO(json.dumps(payload))

    def test_valid_and_negative_funding(self):
        result = fetch('https://example.test', ['lastFundingRate'], [],
                       self.response({'symbol': 'BTCUSDT', 'lastFundingRate': '-0.0001'}))
        self.assertEqual(result['status'], 'ok')

    def test_missing_is_not_zero(self):
        result = fetch('https://example.test', ['price'], [], self.response({'symbol': 'BTCUSDT'}))
        self.assertEqual(result['status'], 'missing_data')
        self.assertIsNone(result['data'])

    def test_invalid_number(self):
        result = fetch('https://example.test', ['price'], [],
                       self.response({'symbol': 'BTCUSDT', 'price': 'NaN'}))
        self.assertEqual(result['error']['kind'], 'invalid_data')

    def test_regional_block_no_retry(self):
        def blocked(*a, **kw):
            raise HTTPError(a[0].full_url, 451, 'blocked', {}, None)
        result = fetch('https://example.test', [], [], blocked)
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['error']['http_status'], 451)

    def test_network_retry_bounded(self):
        def offline(*a, **kw):
            raise URLError('offline')
        result = fetch('https://example.test', [], [], offline, lambda _: None)
        self.assertEqual(result['attempts'], 3)
        self.assertIsNone(result['data'])


if __name__ == '__main__':
    unittest.main()
