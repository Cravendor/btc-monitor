"""Optional keyless CoinGecko BTC/USD ATH benchmark, separate from USDT routes."""
import json
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request, HTTPRedirectHandler, build_opener
from .market_scenarios import iso, number, time_ms

URL = ('https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&'
       'market_data=true&community_data=false&developer_data=false&sparkline=false')
MAX_BYTES = 1048576


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate(payload, as_of):
    now = time_ms(as_of)
    if payload.get('id') != 'bitcoin' or payload.get('symbol') != 'btc':
        raise ValueError('wrong asset')
    data = payload['market_data']
    current, ath = number(data['current_price']['usd']), number(data['ath']['usd'])
    updated = time_ms(data['last_updated'])
    ath_at = time_ms(data['ath_date']['usd'])
    if not (0 < current <= ath and -60000 <= now-updated <= 3600000 and 0 < ath_at <= updated):
        raise ValueError('invalid or stale benchmark')
    to_ath, from_ath = number((ath/current-1)*100), number((current/ath-1)*100)
    return {'status': 'ok', 'provider': 'CoinGecko', 'asset': 'bitcoin', 'unit': 'USD',
            'scope': 'provider_aggregated_spot_reference', 'price': current, 'ath': ath,
            'source_at': iso(updated), 'ath_at': iso(ath_at), 'valid_until': iso(updated+3600000),
            'to_ath_pct': to_ath, 'from_ath_pct': from_ath,
            'source_url': URL}


def fetch_reference(as_of, opener=None):
    """One bounded free request, no signup, token, retry or paid fallback."""
    unavailable = {'status': 'unavailable', 'reason': 'ATH-referentie niet toegankelijk of niet geldig.'}
    try:
        opener = opener or build_opener(NoRedirect())
        request = Request(URL, headers={'User-Agent': 'BTC-public-dashboard/1.0', 'Accept': 'application/json'})
        with opener.open(request, timeout=8) as response:
            body = response.read(MAX_BYTES+1)
        if len(body) > MAX_BYTES: raise ValueError('oversized response')
        return validate(json.loads(body.decode('utf-8')), as_of)
    except (URLError, OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return unavailable
