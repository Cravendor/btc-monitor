"""Bounded, falsifiable forming-impulse hypotheses, never a preferred count.

Every suffix of 2..5 confirmed pivots ending at the latest pivot is retained.
No outcome-based pivot selection, inferred degree, historical flow or probability.
"""
import hashlib
import json
from scripts.elliott_completion import closed_rows
from scripts.elliott_history import floor_time
from scripts.elliott_rules import confirmed_pivots
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS

MODEL = 'elliott_forming_impulse_inventory_v1'


def hypothesis(rows, points, tf):
    """Check a fixed prefix and the unconfirmed following price leg."""
    legs = len(points)-1
    sign = 1 if points[0]['kind']=='low' else -1
    p = [sign*x['price'] for x in points]
    next_leg = legs+1
    next_sign = sign * (-1 if next_leg%2==0 else 1)
    checks = []

    def check(rule, passed, detail):
        checks.append(dict(rule=rule, result='getoetst' if passed else 'geschonden', detail=detail))

    def interval(start, end=None):
        return [r for r in rows if r['open_time_ms']>points[start]['open_time_ms'] and
                (end is None or r['open_time_ms']<=points[end]['open_time_ms'])]

    def minimum(part):
        return min(r['low'] if sign==1 else -r['high'] for r in part)

    # The numbering is a hypothesis: even the first leg is not certified wave 1.
    check('richtingen', all((p[i+1]-p[i])*(1 if i%2==0 else -1)>0 for i in range(legs)),
          'Alle opeenvolgende bevestigde pivots, zonder punten over te slaan.')
    if legs>=2:
        check('golf_2_begin_1', minimum(interval(1,2))>p[0],
              'Alle wicks van het gevormde tweede been tegen het beginpunt.')
    if legs>=3:
        check('golf_3_voorbij_1', p[3]>p[1], 'Gevormd derde pivotbeen moet voorbij het eerste eindigen.')
    if legs>=4:
        check('golf_4_geen_overlap_1', minimum(interval(3,4))>p[1],
              'Alle wicks van het gevormde vierde been buiten golf-1-prijsgebied.')
    for i, point in enumerate(points[:-1]):
        terminal = 1 if point['kind']=='high' else -1
        check('vast_anker_'+str(i), not any((r['high'] if terminal==1 else -r['low'])>
                                          terminal*point['price'] for r in interval(i,i+1)),
              'Geen wick voorbij dit vaste anker tijdens het volgende gevormde been.')
    following = interval(legs)
    last = points[-1]
    terminal_sign = 1 if last['kind']=='high' else -1
    check('vast_eindanker', not any((r['high'] if terminal_sign==1 else -r['low'])>
                                   terminal_sign*last['price'] for r in following),
          'Een latere wick voorbij het vaste laatste pivotanker verwerpt deze vaste variant; hernummering is een andere hypothese.')
    live = max(following, key=lambda r: next_sign*(r['high'] if next_sign==1 else r['low']))
    live_price = live['high'] if next_sign==1 else live['low']
    if next_leg==2:
        check('lopend_2_begin_1', minimum(following)>p[0], 'Ook de nog onbevestigde correctie mag het begin niet raken.')
    if next_leg==4:
        check('lopend_4_geen_overlap_1', minimum(following)>p[1], 'Overlap van een lopend vierde been telt intrabar.')
    if next_leg==5:
        length_1, length_3 = abs(p[1]-p[0]), abs(p[3]-p[2])
        check('lopend_5_golf_3_niet_kortste', length_3>=min(length_1, abs(live_price-last['price'])),
              'Als 1 en het reeds waargenomen vijfde been langer zijn dan 3, is deze vaste variant ongeldig.')
    for rule in ('patroonfamilie_en_graad', 'interne_subgolven', 'eindpunt_lopend_been', 'volume_en_momentum_bij_anker'):
        checks.append(dict(rule=rule, result='niet toetsbaar', detail='Niet afgeleid uit alleen deze koerspivots.'))
    if legs<4:
        checks.append(dict(rule='golf_3_niet_kortste',result='niet toetsbaar',detail='Nog geen waargenomen vijfde been; geen verhouding als voldaan ingevuld.'))
    identity = dict(model=MODEL,timeframe=tf,pattern='standard_impulse_prefix',points=points)
    key = hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]
    return dict(id=key,pattern='standard_impulse_prefix',direction='up' if sign==1 else 'down',
                points=points,completed_pivot_legs=legs,proposed_live_leg=next_leg,
                proposed_live_direction='up' if next_sign==1 else 'down',
                live_extreme=dict(price=live_price,open_time_ms=live['open_time_ms'],confirmed=False),
                anchors_known_at=iso(max(x['confirmed_at_ms'] for x in points)),checks=checks,
                status='invalid' if any(x['result']=='geschonden' for x in checks) else 'unresolved_price_prefix',
                wave_certification='unproven',probability=None)


def build(rows, tf, as_of):
    out = dict(model_version=MODEL,timeframe=tf,as_of=as_of,status='unavailable',
               selection='all_latest_pivot_suffixes_2_to_5',candidates=[],preferred_id=None,
               current_wave=None,probability=None,wave_certification='unproven')
    try:
        data = closed_rows(rows,tf,as_of)
        if not data:
            raise ValueError('no_closed_candles')
        points = confirmed_pivots(data)
        boundary = floor_time(time_ms(as_of),tf)
        closed = data[-1]['open_time_ms']+PERIOD_MS[tf]
        out.update(status='assessed',closed_through=iso(closed),
                   scope='current_closed_window' if closed==boundary else 'historical_closed_window',
                   pivot_count=len(points))
        for count in range(2,min(5,len(points))+1):
            out['candidates'].append(hypothesis(data,points[-count:],tf))
        return out
    except (ValueError,KeyError,TypeError,OverflowError,IndexError) as exc:
        out.update(status='unavailable',reason=str(exc),candidates=[])
        return out
