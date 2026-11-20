"""Read-only USD order card for the mobile dashboard."""
import json
import re
from math import isfinite
from pathlib import Path

from scripts.market_scenarios import STEP, time_ms

ASSETS = Path(__file__).resolve().parents[1] / 'web'


def snapshot(feed, result, now):
    missing = {'reason': 'Actuele 4H-data, futuresprijs of USD-omrekening ontbreekt.'}
    if result['status'] != 'ready' or result['price'] is None:
        return missing
    m = feed['measurements'][0]
    try:
        stable = m['metrics']['stablecoins']
        fx = stable['data']['USDT']
        rate = float(fx['data']['price_usd'])
        fx_time = time_ms(re.sub(r'(\.\d{6})\d+', r'\1', fx['data']['source_time']))
        ticker_time = int(m['metrics']['futures_price']['data']['ts'])
        expires = min(time_ms(result['valid_until']), fx_time + 3600000, ticker_time + 3600000)
        if (stable['status'] != 'ok' or fx['status'] != 'ok' or not isfinite(rate)
                or rate <= 0 or fx_time > time_ms(now) + 60000 or expires <= time_ms(now)):
            return missing
        end = time_ms(result['interval_end'])
        rows = sorted((r for r in m['metrics']['candles_4h']['data']['candles']
                       if end - 21 * STEP <= r['open_time_ms'] < end),
                      key=lambda r: r['open_time_ms'])
        history, breakout, retest = rows[:-2], rows[-2], rows[-1]
        card = {'price': result['price'] * rate, 'rate': rate, 'expires': expires,
                'at': result['snapshot_at'], 'close': float(retest['close']) * rate,
                'volume_ratio': result['volume_ratio'], 'deltas': result['provider_deltas'],
                'support': min(float(r['low']) for r in rows[-8:]) * rate,
                'resistance': max(float(r['high']) for r in rows[-8:]) * rate,
                'reason': 'Geen bevestigde 4H-uitbraak met terugtest.'}
        buffer = result['buffer']
        for direction in (1, -1):
            edge = 'high' if direction == 1 else 'low'
            other = 'low' if direction == 1 else 'high'
            # Last eight bars define the range; older bars supply independent targets.
            level = direction * max(direction * float(r[edge]) for r in history[-8:])

            def distance(row, field):
                return direction * (float(row[field]) - level)
            if not (distance(breakout, 'close') > buffer and distance(retest, other) <= buffer
                    and distance(retest, 'close') > 0):
                continue
            stop = float(retest[other]) - direction * buffer
            if direction * (level - stop) <= 0:
                continue
            levels = [float(r[edge]) for r in history[:-8]
                      if direction * (float(r[edge]) - level) > buffer]
            if not levels:
                card['reason'] = 'Terugtest bevestigd. Een eerder verhandeld doel ontbreekt.'
                continue
            target = min(levels, key=lambda p: abs(p-level))
            card.update(side=direction, entry=level*rate, retest_buffer=buffer*rate, stop=stop*rate, target=target*rate)
        return card
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return missing


def render(feed, result, now):
    data = json.dumps(snapshot(feed, result, now), allow_nan=False).replace('<', '\\u003c')
    template = (ASSETS / 'swing-order.html').read_text(encoding='utf-8')
    logic = (ASSETS / 'swing-order.js').read_text(encoding='utf-8')
    return template.replace('/*SNAPSHOT*/', data).replace('/*LOGIC*/', logic)
