"""Auditable standard-impulse price candidates, never complete wave certification.

Only strict pivots with two closed candles on either side are selected. Internal
5-3-5-3-5 is not inferred from six pivots. Other pattern families are not rescued
by relaxing these rules. All lengths use absolute prices at a single degree.
"""
from math import isfinite


def impulse_checks(points, direction):
    if direction not in ('up', 'down') or len(points) != 6:
        raise ValueError('six pivots and direction required')
    sign = 1 if direction == 'up' else -1
    p = [float(x['price']) * sign for x in points]
    if not all(isfinite(float(x['price'])) and float(x['price'])>0 for x in points):
        raise ValueError('finite prices required')
    lengths = [abs(p[i+1]-p[i]) for i in range(5)]
    def check(rule, passed, detail):
        return dict(rule=rule, result='getoetst' if passed else 'geschonden', detail=detail)
    checks = [
        check('chronologie', all(a['open_time_ms'] < b['open_time_ms'] for a,b in zip(points,points[1:])), 'Strikt oplopende pivot-candle-openingen; geen onbekende volgorde binnen één candle.'),
        check('richtingen_1_2_3_4_5', all((p[i+1]-p[i]) * (1 if i%2==0 else -1) > 0 for i in range(5)), 'Alle vijf benen moeten de standaard impuls-/correctierichting hebben.'),
        check('golf_2_begin_1', p[2] > p[0], f'Golf-2-extremum {points[2]["price"]}; begin golf 1 {points[0]["price"]}. Strikte grens voor deze kandidaat.'),
        check('golf_3_voorbij_1', p[3] > p[1], f'Golf-3-einde {points[3]["price"]}; golf-1-einde {points[1]["price"]}.'),
        check('golf_3_niet_kortste', lengths[2] >= min(lengths[0], lengths[4]), f'Absolute prijslengtes golf 1/3/5: {lengths[0]}, {lengths[2]}, {lengths[4]}. Alleen gevormde pivotbenen.'),
        check('golf_4_geen_overlap_1', p[4] > p[1], f'Golf-4-extremum {points[4]["price"]}; golf-1-grens {points[1]["price"]}. Highs/lows, niet uitsluitend slot.'),
        dict(rule='interne_5_3_5_3_5', result='niet toetsbaar', detail='Vereist geschikte subgolven en patroonvalidatie. Zes pivotpunten bewijzen dit niet.'),
    ]
    return checks


def confirmed_pivots(rows):
    pivots = []
    for i in range(2, len(rows)-2):
        c = rows[i]
        others = rows[i-2:i] + rows[i+1:i+3]
        low = all(c['low'] < x['low'] for x in others)
        high = all(c['high'] > x['high'] for x in others)
        # An outside candle can contain both extremes in unknown tick order.
        if low == high:
            continue
        kind, value = ('low', c['low']) if low else ('high', c['high'])
        point = dict(open_time_ms=c['open_time_ms'], confirmed_at_ms=rows[i+2]['open_time_ms']+(rows[i+1]['open_time_ms']-c['open_time_ms']),
                     kind=kind, price=value)
        if pivots and pivots[-1]['kind'] == kind:
            if (value < pivots[-1]['price']) if low else (value > pivots[-1]['price']):
                pivots[-1] = point
        else:
            pivots.append(point)
    return pivots


def price_checks(rows, points, direction):
    """Standard-impulse outline plus every intervening wick at this scale."""
    checks = impulse_checks(points, direction)
    # Inspect ALL intermediate extrema, not just selected pivot endpoints.
    sign = 1 if direction == 'up' else -1
    p = [x['price']*sign for x in points]
    def extreme(lo, hi):
        values = [r['low'] if sign==1 else -r['high'] for r in rows
                  if points[lo]['open_time_ms'] < r['open_time_ms'] <= points[hi]['open_time_ms']]
        return min(values)
    for rule, passed, detail in (
        ('golf_2_interval', extreme(1,2)>p[0], 'Alle candle-extremen tussen golf 1 en 2 tegen beginpunt gecontroleerd.'),
        ('golf_4_interval', extreme(3,4)>p[1], 'Alle candle-extremen tussen golf 3 en 4 tegen golf-1-prijsgebied gecontroleerd.'),
    ):
        checks.append(dict(rule=rule, result='getoetst' if passed else 'geschonden', detail=detail))
    return checks


def assess_candidates(rows, timeframe):
    pivots = confirmed_pivots(rows)
    candidates = []
    # Fixed selection, independent of subsequent price and rule outcomes.
    for offset in range(min(2, max(0, len(pivots)-5))):
        end = len(pivots)-offset
        points = pivots[end-6:end]
        direction = 'up' if points[0]['kind']=='low' else 'down'
        checks = price_checks(rows, points, direction)
        violated = any(c['result']=='geschonden' for c in checks)
        candidates.append(dict(id='candidate_'+str(offset+1), pattern='standard_impulse', timeframe=timeframe,
                               direction=direction, points=points, checks=checks,
                               status='invalid' if violated else 'provisional_price_pattern',
                               length_measure='absolute_price', invalidation_price=points[0]['price'],
                               invalidation_role='Beginpunt van deze historische kandidaat; geen stopprijs voor een volgende correctie.',
                               note='Historische kandidaat; geen bewijs dat de huidige koers in een volgende specifieke golf zit.'))
    return dict(status='candidates' if candidates else 'insufficient_data', candidates=candidates,
                pivot_count=len(pivots), current_wave=None,
                reason='Geen automatisch bevestigde huidige telling. Subgolven en alternatieve patroonfamilies niet vastgesteld.')
