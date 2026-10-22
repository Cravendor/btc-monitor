"""Bounded public REST backfill of the latest closed UTC 4H futures delta."""
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

INTERVAL = 14_400_000
URL = 'https://api.bitget.com/api/v2/mix/market/fills-history'


def positive(value):
    value = Decimal(str(value))
    if not value.is_finite() or value <= 0:
        raise ValueError('Expected positive finite trade number')
    return value


def collect_cvd(candle_metric, now_ms=None, opener=urlopen, sleep=time.sleep,
                max_pages=1500, budget_seconds=180):
    now_ms = now_ms if now_ms is not None else int(time.time()*1000)
    end = now_ms // INTERVAL * INTERVAL
    start = end - INTERVAL
    result = dict(status='missing_data', value=None, data=None, url=URL,
                  observed_at=datetime.now(timezone.utc).isoformat(),
                  interval_start_ms=start, interval_end_ms=end, unit='BTC',
                  method='Interval trade delta: buy size minus sell size; resets each 4H',
                  coverage='unverified', pages=0)
    started = time.monotonic()
    try:
        if candle_metric.get('status') != 'ok':
            raise ValueError('Closed candle unavailable')
        candle = next(c for c in candle_metric['data']['candles'] if c['open_time_ms'] == start)
        expected = Decimal(str(candle['base_volume_btc']))
        if not expected.is_finite() or expected < 0:
            raise ValueError('Invalid candle volume')
        seen = {}
        buy = sell = Decimal(0)
        quote = Decimal(0)
        cursor = None
        duplicates = 0
        exhausted = False
        for page in range(max_pages):
            if time.monotonic()-started >= budget_seconds:
                raise ValueError('Backfill time budget exceeded')
            params = dict(symbol='BTCUSDT', productType='USDT-FUTURES', limit=1000,
                          startTime=start, endTime=end-1)
            if cursor is not None:
                params['idLessThan'] = cursor
            sleep(.12)  # below public 10 requests/s limit
            with opener(Request(URL+'?'+urlencode(params), headers={'User-Agent':'btc-public-monitor/1.0'}), timeout=15) as response:
                payload = json.load(response)
            result['pages'] = page+1
            if payload.get('code') != '00000' or not isinstance(payload.get('data'), list):
                raise ValueError('Invalid/API error trade response: '+str(payload.get('code')))
            rows = payload['data']
            if not rows:
                exhausted = True
                break
            ids = []
            for row in rows:
                tid = int(row['tradeId'])
                ts = int(row['ts'])
                price, size = positive(row['price']), positive(row['size'])
                side = str(row['side']).lower()
                if tid <= 0 or row['symbol'] != 'BTCUSDT' or side not in ('buy','sell') or not start <= ts < end:
                    raise ValueError('Invalid trade identity, side or interval')
                normalized = (ts, price, size, side)
                ids.append(tid)
                if tid in seen:
                    if seen[tid] != normalized:
                        raise ValueError('Conflicting duplicate trade')
                    duplicates += 1
                    continue
                if cursor is not None and tid >= cursor:
                    raise ValueError('Pagination cursor not respected')
                seen[tid] = normalized
                if side == 'buy':
                    buy += size
                else:
                    sell += size
                quote += price*size
            next_cursor = min(ids)
            if cursor is not None and next_cursor >= cursor:
                raise ValueError('Pagination stalled')
            cursor = next_cursor
            # Even short pages require a terminal empty page: never assume a cap means completion.
        if not exhausted:
            raise ValueError('Backfill page limit exceeded')
        total = buy+sell
        # Tight absolute tolerances cover only candle serialization/rounding.
        base_error = abs(total-expected)
        quote_error = abs(quote-Decimal(str(candle['quote_volume_usdt'])))
        result.update(trade_count=len(seen), duplicates=duplicates,
                      collected_volume_btc=str(total), candle_volume_btc=str(expected),
                      base_volume_error_btc=str(base_error), quote_volume_error_usdt=str(quote_error),
                      pagination_exhausted=True)
        if base_error > Decimal('0.00000001') or quote_error > Decimal('0.01'):
            raise ValueError('Trade/candle volume mismatch: coverage unverified')
        data = dict(delta_btc=str(buy-sell), buy_volume_btc=str(buy), sell_volume_btc=str(sell),
                    interval_start_ms=start, interval_end_ms=end, trade_count=len(seen),
                    first_trade_ms=min((v[0] for v in seen.values()), default=None),
                    last_trade_ms=max((v[0] for v in seen.values()), default=None))
        result.update(status='ok', value=str(buy-sell), data=data,
                      coverage='complete_reconciled',
                      limitation='Provider pagination and candle reconciliation; no exchange sequence proof. Bitget futures only, not spot or market-wide CVD.')
    except Exception as exc:
        result['reason'] = str(exc)[:250]
    return result
