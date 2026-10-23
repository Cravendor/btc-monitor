"""Public, credential-free supplementary snapshots. Never starts paid services."""
import json
import math
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE = 'https://api.bitget.com/api/v2/'


def source_timestamp(value):
    """Parse explicit-zone source times consistently on Python 3.9+.

    Coinbase supplies nanoseconds; datetime stores microseconds. Truncate only
    fractional precision, preserving the date and UTC offset for age/skew checks.
    """
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})', value)
    if match is None:
        raise ValueError('Invalid source timestamp or missing timezone')
    base, fraction, zone = match.groups()
    fraction = '.' + fraction[:6].ljust(6, '0') if fraction else ''
    zone = '+00:00' if zone == 'Z' else zone
    return datetime.fromisoformat(base + fraction + zone).timestamp()


def number(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Expected positive finite number')
    return value


def request(url, transform, bitget=False):
    result = {'url': url, 'observed_at': datetime.now(timezone.utc).isoformat(),
              'status': 'error', 'data': None}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'btc-public-monitor/1.0'}), timeout=15) as response:
            payload = json.load(response)
        if bitget:
            if payload.get('code') != '00000':
                raise ValueError('Bitget API error: ' + str(payload.get('code')))
            payload = payload['data']
        result.update(status='ok', data=transform(payload))
    except Exception as exc:
        result['error'] = str(exc)[:200]
    return result


def candles(rows):
    boundary = int(datetime.now(timezone.utc).timestamp() * 1000) // 14400000 * 14400000
    values = {}
    for row in rows:
        ts = int(row[0])
        if ts % 14400000 or ts >= boundary:
            continue
        prices = [number(x) for x in row[1:5]]
        volumes = [float(x) for x in row[5:7]]
        if len(prices) != 4 or len(volumes) != 2 or any(not math.isfinite(v) or v < 0 for v in volumes):
            raise ValueError('Invalid candle')
        o, h, l, c = prices
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError('Invalid OHLC range')
        values[ts] = {'open_time_ms': ts, 'open': o, 'high': h, 'low': l, 'close': c,
                      'base_volume_btc': volumes[0], 'quote_volume_usdt': volumes[1]}
    ordered = [values[t] for t in sorted(values)]
    if not ordered or ordered[-1]['open_time_ms'] != boundary - 14400000:
        raise ValueError('Latest closed 4H candle missing')
    gaps = [ordered[i]['open_time_ms'] for i in range(1, len(ordered))
            if ordered[i]['open_time_ms'] - ordered[i-1]['open_time_ms'] != 14400000]
    return {'candles': ordered, 'gap_count': len(gaps), 'closed_only': True, 'interval': '4H'}


def depth(book):
    bids = sorted([(number(p), number(q)) for p, q, *rest in book['bids']], reverse=True)
    asks = sorted([(number(p), number(q)) for p, q, *rest in book['asks']])
    if not bids or not asks or bids[0][0] >= asks[0][0]:
        raise ValueError('Empty or crossed orderbook')
    mid = (bids[0][0] + asks[0][0]) / 2
    bands = {}
    for fraction in (.001, .005, .01):
        b = sum(p*q for p, q in bids if p >= mid*(1-fraction))
        a = sum(p*q for p, q in asks if p <= mid*(1+fraction))
        bands[str(fraction*100)] = {'bid_notional_usdt': b, 'ask_notional_usdt': a,
            'imbalance': (b-a)/(b+a) if b+a else None,
            'bid_band_covered': bids[-1][0] <= mid*(1-fraction),
            'ask_band_covered': asks[-1][0] >= mid*(1+fraction)}
    return {'source_ts_ms': int(book['ts']), 'mid_usdt': mid,
            'spread_bps': (asks[0][0]-bids[0][0])/mid*10000,
            'bands_pct': bands, 'bid_levels': len(bids), 'ask_levels': len(asks),
            'scope': 'Returned levels only; incomplete bands are lower bounds, not full market depth.'}


def ticker(rows):
    row = next(r for r in rows if r['symbol'] == 'BTCUSDT')
    return {'price_usdt': number(row['lastPr']), 'source_ts_ms': int(row['ts'])}


def coinbase(row):
    return {'price_usd': number(row['price']), 'source_time': row['time']}


def stable(row):
    p = number(row['price'])
    return {'price_usd': p, 'depeg_pct': (p-1)*100, 'source_time': row['time']}


def derived(sources, calculation):
    result = {'status': 'missing_data', 'data': None, 'sources': sources}
    if all(s['status'] == 'ok' for s in sources.values()):
        try:
            result.update(status='ok', data=calculation({k:v['data'] for k,v in sources.items()}))
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            result['error'] = str(exc)[:200]
    return result


def collect_extra(metrics):
    extra = {}
    extra['candles_4h'] = request(BASE+'mix/market/candles?symbol=BTCUSDT&productType=USDT-FUTURES&granularity=4H&limit=100', candles, True)
    extra['orderbook_depth'] = request(BASE+'mix/market/merge-depth?symbol=BTCUSDT&productType=USDT-FUTURES&precision=scale0&limit=100', depth, True)
    spot = request(BASE+'spot/market/tickers?symbol=BTCUSDT', ticker, True)
    cb = request('https://api.exchange.coinbase.com/products/BTC-USD/ticker', coinbase)
    usdt = request('https://api.exchange.coinbase.com/products/USDT-USD/ticker', stable)
    usdc_pair = request(BASE+'spot/market/tickers?symbol=USDCUSDT',
                        lambda rows: {'price_usdt': number(next(r for r in rows if r['symbol']=='USDCUSDT')['lastPr']),
                                      'source_ts_ms': int(next(r for r in rows if r['symbol']=='USDCUSDT')['ts'])}, True)
    def usdc_price(s):
        ts = s['pair']['source_ts_ms']/1000
        usd_ts = source_timestamp(s['usdt']['source_time'])
        if abs(ts-usd_ts)>120 or datetime.now(timezone.utc).timestamp()-min(ts,usd_ts)>180:
            raise ValueError('Stale or unsynchronised stablecoin sources')
        price = s['pair']['price_usdt'] * s['usdt']['price_usd']
        return {'price_usd': price, 'depeg_pct': (price-1)*100,
                'method': 'Bitget USDC-USDT times Coinbase USDT-USD'}
    usdc = derived({'pair': usdc_pair, 'usdt': usdt}, usdc_price)
    extra['spot_price'] = spot
    extra['stablecoins'] = {'status': 'ok' if all(v['status']=='ok' for v in (usdt,usdc)) else 'partial',
                           'data': {'USDT': usdt, 'USDC': usdc},
                           'scope': 'USD prices/depeg only; not supply, exchange balances or buying power.'}
    def premium(s):
        times = [s['spot']['source_ts_ms']/1000] + [source_timestamp(s[k]['source_time']) for k in ('coinbase','usdt')]
        if max(times)-min(times) > 120 or datetime.now(timezone.utc).timestamp()-min(times) > 180:
            raise ValueError('Stale or unsynchronised price sources')
        reference = s['spot']['price_usdt'] * s['usdt']['price_usd']
        return {'premium_pct': (s['coinbase']['price_usd']/reference-1)*100,
                'method': 'Coinbase BTC-USD versus Bitget BTC-USDT converted using Coinbase USDT-USD; proxy, not standard Coinbase/Binance index.',
                'max_source_skew_seconds': max(times)-min(times)}
    extra['coinbase_premium_proxy'] = derived({'spot': spot, 'coinbase': cb, 'usdt': usdt}, premium)
    def basis(s):
        row=s['futures']
        if abs(datetime.now(timezone.utc).timestamp()-int(row['ts'])/1000) > 180:
            raise ValueError('Stale futures source')
        return {'basis_pct': (number(row['markPrice'])/number(row['indexPrice'])-1)*100,
                'mark_price_usdt': number(row['markPrice']), 'index_price_usdt': number(row['indexPrice']),
                'source_ts_ms': int(row['ts']), 'method': 'Bitget perpetual mark/index premium; not dated futures annualised basis.'}
    extra['futures_basis'] = derived({'futures': metrics['futures_price']}, basis)
    return extra
