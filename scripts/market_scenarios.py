"""Read-only, uncalibrated 4H price scenarios from closed Bitget candles.

Levels are attention thresholds, not orders, probabilities or position sizing.
The reference range and volatility exclude the candle used for confirmation.
"""
from datetime import datetime, timezone
from math import isfinite
from statistics import mean

STEP = 14400000
MAX_AGE_SECONDS = 3600
MODEL = 'closed_4h_range20_atr14_v1'


def time_ms(value):
    if not isinstance(value, str):
        raise ValueError('missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp without timezone')
    return int(parsed.timestamp() * 1000)


def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError('invalid number')
    result = float(value)
    if not isfinite(result):
        raise ValueError('non-finite number')
    return result


def iso(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()


def build_scenarios(feed, as_of):
    """Never replace a missing latest snapshot with an older green one."""
    unavailable = {'status': 'unavailable', 'model_version': MODEL,
                   'reason': 'Onvoldoende geldige, actuele 4H-data.', 'scenarios': []}
    try:
        now = time_ms(as_of)
        measurements = feed.get('measurements')
        if not isinstance(measurements, list) or not measurements:
            raise ValueError('Geen marktmeting beschikbaar.')
        m = measurements[0]
        if (m.get('exchange') != 'bitget' or m.get('market') != 'USDT-FUTURES'
                or m.get('symbol') != 'BTCUSDT'):
            raise ValueError('Verkeerde beurs of markt voor deze berekening.')
        started, finished = time_ms(m.get('started_at')), time_ms(m.get('finished_at'))
        if finished < started or now - started > MAX_AGE_SECONDS * 1000 or finished > now + 60000:
            raise ValueError('Marktmeting ouder dan één uur of tijdstempel ongeldig.')
        metric = (m.get('metrics') or {}).get('candles_4h') or {}
        if metric.get('status') != 'ok':
            raise ValueError('De nieuwste 4H-candlebron is niet geldig.')
        observed = time_ms(metric.get('observed_at'))
        if now - observed > MAX_AGE_SECONDS * 1000 or observed > now + 60000:
            raise ValueError('De candlemeting is verouderd of heeft een ongeldige tijd.')
        data = metric.get('data') or {}
        if data.get('interval') != '4H' or data.get('closed_only') is not True:
            raise ValueError('Geen gecontroleerde afgesloten 4H-candles.')
        rows = data.get('candles')
        if not isinstance(rows, list):
            raise ValueError('Candles ontbreken.')
        parsed = {}
        boundary = now // STEP * STEP
        for row in rows:
            t = row.get('open_time_ms')
            if type(t) is not int or t < 0 or t % STEP:
                raise ValueError('Ongeldige candlegrens.')
            o, h, l, c, v = (number(row.get(k)) for k in
                              ('open', 'high', 'low', 'close', 'base_volume_btc'))
            if min(o, h, l, c) <= 0 or v < 0 or l > min(o, c) or h < max(o, c):
                raise ValueError('Ongeldige candleprijzen of volume.')
            # An in-progress candle cannot trigger a confirmed scenario.
            if t >= boundary:
                continue
            item = (t, o, h, l, c, v)
            if t in parsed:
                raise ValueError('Dubbele candles: geen scenario berekend.')
            parsed[t] = item
        recent = sorted(parsed.values())[-21:]
        if len(recent) != 21:
            raise ValueError('Minimaal 21 afgesloten 4H-candles nodig.')
        if recent[-1][0] != boundary - STEP:
            raise ValueError('De laatst afgesloten 4H-candle ontbreekt.')
        if any(b[0] - a[0] != STEP for a, b in zip(recent, recent[1:])):
            raise ValueError('Meetgaten in de 21 benodigde 4H-candles.')
        prior, last = recent[:-1], recent[-1]
        support, resistance = min(c[3] for c in prior), max(c[2] for c in prior)
        tr = [max(c[2] - c[3], abs(c[2] - p[4]), abs(c[3] - p[4]))
              for p, c in zip(prior[-15:-1], prior[-14:])]
        atr = mean(tr)
        if atr <= 0 or support >= resistance:
            raise ValueError('Geen bruikbare prijsrange of volatiliteit.')
        buffer = atr * 0.1
        up, down = resistance + buffer, support - buffer
        if down - 2 * atr <= 0:
            raise ValueError('Volatiliteit levert onbruikbare projectieniveaus op.')
        close = last[4]
        state = 'bullish_breakout' if close > up else 'bearish_breakdown' if close < down else 'range'
        average_volume = mean(c[5] for c in prior)
        ratio = last[5] / average_volume if average_volume > 0 else None
        volume_24h = sum(c[5] for c in recent[-6:])
        previous_24h = sum(c[5] for c in recent[-12:-6])
        scenarios = [
            {'id': 'bullish_breakout', 'label': 'Bullish · uitbraak', 'trigger': up,
             'invalidation': resistance - buffer, 'targets': [up + atr, up + 2 * atr],
             'confirmed_by_last_close': state == 'bullish_breakout'},
            {'id': 'range', 'label': 'Zijwaarts · afwachten', 'lower': down, 'upper': up,
             'midpoint': (support + resistance) / 2,
             'confirmed_by_last_close': state == 'range'},
            {'id': 'bearish_breakdown', 'label': 'Bearish · steunverlies', 'trigger': down,
             'invalidation': support + buffer, 'targets': [down - atr, down - 2 * atr],
             'confirmed_by_last_close': state == 'bearish_breakdown'}]
        cvd = m.get('cvd_4h') or {}
        deltas = {}
        for market in ('spot', 'usdt_futures'):
            proof = (cvd.get('markets') or {}).get(market) or {}
            try:
                if (proof.get('status') == 'ok' and proof.get('coverage_verified') is True
                        and proof.get('coverage_scope') == 'bitget_public_history_only'
                        and proof.get('coverage_method') == 'bitget_history_exhaustion_and_exact_volume_v1'
                        and proof.get('exchange') == 'bitget' and proof.get('symbol') == 'BTCUSDT'
                        and proof.get('market') == market and proof.get('unit') == 'BTC'
                        and proof.get('interval_start_ms') == last[0]
                        and proof.get('interval_end_ms') == last[0] + STEP):
                    deltas[market] = number(proof.get('validated_delta_btc'))
            except (ValueError, TypeError, OverflowError):
                pass
        price = None
        ticker = (m.get('metrics') or {}).get('futures_price') or {}
        try:
            ticker_data = ticker.get('data') or {}
            ts = number(ticker_data.get('ts'))
            value = number(ticker_data.get('lastPr'))
            if ticker.get('status') == 'ok' and value > 0 and -60000 <= now - ts <= MAX_AGE_SECONDS * 1000:
                price = value
        except (ValueError, TypeError, OverflowError):
            pass
        return {'status': 'ready', 'model_version': MODEL, 'source': m.get('collection_source'),
                'snapshot_at': m['finished_at'],
                'valid_until': iso(min(started + MAX_AGE_SECONDS * 1000, boundary + STEP)),
                'interval_start': iso(last[0]), 'interval_end': iso(last[0] + STEP),
                'range_start': iso(prior[0][0]), 'range_end': iso(last[0]),
                'last_close': close, 'price': price, 'support': support, 'resistance': resistance,
                'atr14': atr, 'buffer': buffer, 'volume_ratio': ratio, 'volume': last[5],
                'volume_24h': volume_24h, 'previous_24h_volume': previous_24h,
                'volume_24h_ratio': volume_24h / previous_24h if previous_24h > 0 else None,
                'prior20_volume': average_volume, 'state': state, 'scenarios': scenarios,
                'provider_deltas': deltas, 'confidence': 'uncalibrated_price_scenario'}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        # Return a useful, non-sensitive explanation without leaking raw errors.
        return unavailable
