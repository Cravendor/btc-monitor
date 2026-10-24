"""Optional free sentiment context. Providers are never silently mixed."""
import json
from datetime import datetime, timezone
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request, build_opener
from scripts.ath_reference import NoRedirect
from scripts.market_scenarios import iso, number, time_ms

SOURCES = (
    ('CoinMarketCap', 'https://pro-api.coinmarketcap.com/public-api/v3/fear-and-greed/latest',
     'https://coinmarketcap.com/charts/fear-and-greed-index/'),
    ('Alternative.me', 'https://api.alternative.me/fng/?limit=1',
     'https://alternative.me/crypto/fear-and-greed-index/'),
)


def validate(payload, provider, as_of):
    if provider not in {x[0] for x in SOURCES}:
        raise ValueError('unknown provider')
    data = payload['data']
    if provider == 'Alternative.me':
        if (payload.get('metadata') or {}).get('error'):
            raise ValueError('provider error')
        data = data[0]
        timestamp = number(data['timestamp']) * 1000
    else:
        if (payload.get('status') or {}).get('error_code') not in (None, 0):
            raise ValueError('provider error')
        raw = data.get('update_time', data.get('timestamp'))
        timestamp = time_ms(raw) if isinstance(raw, str) and 'T' in raw else number(raw) * 1000
    value = number(data['value'])
    if not 0 <= value <= 100 or value != int(value):
        raise ValueError('invalid index')
    if not -60000 <= time_ms(as_of) - timestamp < 36 * 3600000:
        raise ValueError('stale sentiment')
    label = data['value_classification']
    if not isinstance(label, str) or not label.strip():
        raise ValueError('missing category')
    return dict(status='ok', provider=provider, value=int(value), label=label,
                source_at=iso(timestamp), valid_until=iso(timestamp + 36 * 3600000),
                source_url=next(x[2] for x in SOURCES if x[0] == provider))


def fetch_reference(as_of, opener=None):
    opener = opener or build_opener(NoRedirect())
    for provider, url, _ in SOURCES:
        try:
            request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'BTC-public-dashboard/1.0'})
            with opener.open(request, timeout=6) as response:
                body = response.read(65537)
            if len(body) > 65536:
                raise ValueError('oversized response')
            result = validate(json.loads(body.decode('utf-8')), provider, as_of)
            result['fallback'] = provider != 'CoinMarketCap'
            return result
        except (OSError, URLError, HTTPException, ValueError, KeyError, TypeError,
                AttributeError, OverflowError, IndexError):
            continue
    return {'status': 'unavailable', 'reason': 'Beide gratis sentimentbronnen ontbreken of zijn ongeldig.'}
