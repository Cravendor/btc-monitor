"""Conditional, same-instrument routes; never infer a bull cycle or lifetime ATH."""
from .market_scenarios import build_scenarios, fibonacci_range, iso, number, time_ms
from .native_timeframe_candles import validate_rows

HORIZONS = (('4h', 'Kort · 4H–1D'), ('1d', 'Middellang · dagen tot weken'),
            ('1w', 'Macro · weken tot maanden'))


def change_pct(start, end):
    start, end = number(start), number(end)
    if start <= 0 or end <= 0:
        raise ValueError('positive prices required')
    return number((end / start - 1) * 100)


def route(rows, current, timeframe, label):
    prior = [(c['open_time_ms'], c['open'], c['high'], c['low'], c['close'], c['base_volume_btc'])
             for c in rows[-21:-1]]
    fib = fibonacci_range(prior)
    points = {}

    def add(value, description, kind):
        key = round(value, 1)
        if key > 0:
            item = points.setdefault(key, {'price': key, 'labels': [], 'kinds': []})
            if description not in item['labels']: item['labels'].append(description)
            if kind not in item['kinds']: item['kinds'].append(kind)

    add(min(c[3] for c in prior), 'Low van vorige 20 candles', 'observed_range')
    add(max(c[2] for c in prior), 'High van vorige 20 candles', 'observed_range')
    if fib['status'] == 'calculated':
        for level in fib['retracements']:
            add(level['price'], 'Fib ' + format(level['ratio']*100, '.1f') + '% · ' + level['role'], 'retracement')
        for level in fib['extensions']:
            # Distant extrapolations are not intermediate historical resistance.
            if level['ratio'] <= 1.618:
                add(level['price'], 'Tweepunts-extensie ' + format(level['ratio']*100, '.1f') + '%', 'projection')
    # A pivot is confirmed only after two complete candles on its right.
    for i in range(2, len(rows)-2):
        nearby = rows[i-2:i+3]
        if all(rows[i]['low'] < c['low'] for j, c in enumerate(nearby) if j != 2):
            add(rows[i]['low'], 'Bevestigde pivot-low · candle ' + iso(rows[i]['open_time_ms']), 'observed_pivot')
    ordered = sorted(points.values(), key=lambda x: x['price'])
    upward = []
    for level in (p for p in ordered if p['price'] > current):
        # Pivot lows are fallback references, not automatic upside obstacles.
        if level['kinds'] == ['observed_pivot']: continue
        fallbacks = [dict(p, change_pct=change_pct(level['price'], p['price']))
                     for p in reversed(ordered) if p['price'] < level['price']][:2]
        upward.append(dict(level, distance_pct=change_pct(current, level['price']), rejection_to=fallbacks))
    return {'status': 'ready', 'timeframe': timeframe, 'label': label,
            'reference_price': current, 'unit': 'USDT', 'market': 'USDT-FUTURES', 'exchange': 'bitget',
            'last_closed_at': iso(rows[-1]['open_time_ms'] + {'4h':14400000,'1d':86400000,'1w':604800000}[timeframe]),
            'history_from': iso(rows[0]['open_time_ms']), 'history_candles': len(rows),
            'reference_from': iso(prior[0][0]), 'reference_until': iso(rows[-1]['open_time_ms']),
            'upward': upward[:6], 'fibonacci': fib, 'bull_cycle_confirmed': False,
            'ath': None, 'ath_reason': 'Beperkte candlehistorie bewijst geen all-time high.'}


def build_roadmap(feed, as_of):
    base = build_scenarios(feed, as_of)
    if base['status'] != 'ready' or base['price'] is None:
        return {'status': 'unavailable', 'horizons': [], 'reason': 'Actuele prijs of geldige 4H-bron ontbreekt.'}
    measurement = feed['measurements'][0]
    metrics = measurement.get('metrics') or {}
    native = (metrics.get('multi_timeframe') or {}).get('data') or {}
    output = []
    now = time_ms(as_of)
    for tf, label in HORIZONS:
        try:
            metric = metrics.get('candles_4h') if tf == '4h' else native.get(tf)
            if not metric or metric.get('status') != 'ok': raise ValueError('missing source')
            observed = time_ms(metric.get('observed_at'))
            if not -60000 <= now - observed <= 3600000: raise ValueError('stale source')
            data = metric.get('data') or {}
            if data.get('interval', '').lower() != tf or data.get('closed_only') is not True:
                raise ValueError('wrong interval')
            rows = data.get('candles')
            if not isinstance(rows, list): raise ValueError('missing candles')
            raw = [[c['open_time_ms'], c['open'], c['high'], c['low'], c['close'],
                    c['base_volume_btc'], c.get('quote_volume_usdt', 0)] for c in rows]
            validated = validate_rows(raw, tf, as_of)['candles']
            # Use only the contiguous 24-candle window whose coverage was checked.
            output.append(route(validated[-24:], base['price'], tf, label))
        except (AttributeError, ValueError, TypeError, KeyError, OverflowError):
            output.append({'status': 'unavailable', 'timeframe': tf, 'label': label,
                           'reason': 'Onvoldoende actuele, aaneengesloten native candles.'})
    return {'status': 'ready', 'horizons': output, 'valid_until': base['valid_until']}
