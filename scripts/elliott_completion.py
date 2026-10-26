"""Point-in-time structural endpoint evidence; never Elliott wave certification."""
from scripts.elliott_history import checked, floor_time
from scripts.elliott_rules import confirmed_pivots
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS

MODEL = 'elliott_endpoint_structure_v1'
LABELS = {
    'pivot_only': 'Pivot bevestigd; omslag nog niet structureel bevestigd',
    'opposing_swing_broken': 'Tegengesteld swingniveau doorbroken op slot',
    'pullback_held': 'Terugtest houdt het eindpunt; vervolg ontbreekt',
    'continuation_after_pullback': 'Vervolg na terugtest ondersteunt koersomslag',
    'endpoint_extended': 'Oud eindpunt overschreden; voortzetting waargenomen',
}


def closed_rows(rows, tf, as_of):
    boundary = floor_time(time_ms(as_of), tf)
    result = []
    for row in rows:
        t = row.get('open_time_ms')
        if type(t) is not int:
            raise ValueError('invalid_time')
        if t >= boundary:
            continue
        result.append(checked(row, tf, boundary))
    if any(b['open_time_ms']-a['open_time_ms'] != PERIOD_MS[tf]
           for a,b in zip(result,result[1:])):
        raise ValueError('gap_or_duplicate')
    return result


def assess(rows, tf, as_of, anchor=None):
    """Freeze the opposing swing at anchor recognition; track ordered events.

    Only closed candles count for breaks/continuation. Every later high/low is
    inspected for extension. A pivot is not a wave count; pattern/subdivision
    and degree certification remain separate unmet prerequisites.
    """
    out = dict(model_version=MODEL, timeframe=tf, status='unavailable',
               wave_completion='unproven', probability=None, as_of=as_of)
    try:
        rows = closed_rows(rows, tf, as_of)
        pivots = confirmed_pivots(rows)
        if anchor is None:
            if not pivots:
                raise ValueError('no_confirmed_pivot')
            anchor = pivots[-1]
        if anchor['confirmed_at_ms'] > time_ms(as_of):
            raise ValueError('anchor_not_yet_known')
        # Reconstruct the pivot sequence when this endpoint first became known,
        # so subsequent same-kind pivots cannot move its preselected break level.
        prefix = [r for r in rows if r['open_time_ms']+PERIOD_MS[tf] <= anchor['confirmed_at_ms']]
        known = confirmed_pivots(prefix)
        endpoint = next((p for p in known if all(p[k]==anchor[k]
                        for k in ('open_time_ms','kind','price'))), None)
        if endpoint is None:
            raise ValueError('anchor_not_confirmed_at_this_scale')
        previous = [p for p in known if p['open_time_ms'] < endpoint['open_time_ms']
                    and p['kind'] != endpoint['kind']]
        if not previous:
            raise ValueError('opposing_swing_unavailable')
        level = previous[-1]
        sign = 1 if endpoint['kind']=='high' else -1
        following = [r for r in rows if r['open_time_ms'] > endpoint['open_time_ms']]
        out.update(status='available', endpoint=endpoint, opposing_swing=level,
                   reversal_direction='down' if sign==1 else 'up', stage='pivot_only',
                   closed_through=iso(rows[-1]['open_time_ms']+PERIOD_MS[tf]),
                   break_at=None, pullback_at=None, continuation_at=None,
                   evidence_known_at=iso(anchor['confirmed_at_ms']))
        # Wick violations invalidate this fixed endpoint even if price closes back.
        extended = next((r for r in following if
                         (r['high'] if sign==1 else -r['low']) > sign*endpoint['price']), None)
        if extended:
            out.update(stage='endpoint_extended',
                       extension_candle_at=iso(extended['open_time_ms']),
                       evidence_known_at=iso(max(anchor['confirmed_at_ms'],extended['open_time_ms']+PERIOD_MS[tf])))
            return out
        ready = max(anchor['confirmed_at_ms'],level['confirmed_at_ms'])
        broken = next((r for r in following if r['open_time_ms']+PERIOD_MS[tf] >= ready
                       and sign*r['close'] < sign*level['price']), None)
        if broken is None:
            return out
        broke_at = broken['open_time_ms']+PERIOD_MS[tf]
        out.update(stage='opposing_swing_broken',break_at=iso(broke_at),evidence_known_at=iso(broke_at))
        # First confirmed reversal leg AFTER the break, then the next alternating
        # confirmed pullback. Do not search later for a more convenient sequence.
        legs = [p for p in pivots if p['open_time_ms'] >= broken['open_time_ms']
                and p['kind'] != endpoint['kind'] and p['confirmed_at_ms'] >= broke_at]
        if not legs:
            return out
        leg = legs[0]
        pullbacks = [p for p in pivots if p['open_time_ms'] > leg['open_time_ms']
                     and p['kind']==endpoint['kind'] and p['confirmed_at_ms'] > leg['confirmed_at_ms']]
        if not pullbacks:
            return out
        pullback = pullbacks[0]
        if sign*pullback['price'] >= sign*endpoint['price']:
            # Equal touches do not invalidate the endpoint, but neither prove
            # the strict lower high / higher low required by this model.
            out['pullback_note']='old_endpoint_retested_without_strict_hold'
            return out
        out.update(stage='pullback_held',first_reversal_leg=leg,pullback=pullback,
                   pullback_at=iso(pullback['confirmed_at_ms']),
                   evidence_known_at=iso(pullback['confirmed_at_ms']))
        continuation = next((r for r in rows if r['open_time_ms'] >= pullback['confirmed_at_ms']
                             and sign*r['close'] < sign*leg['price']), None)
        if continuation:
            out.update(stage='continuation_after_pullback',
                       continuation_at=iso(continuation['open_time_ms']+PERIOD_MS[tf]),
                       evidence_known_at=iso(continuation['open_time_ms']+PERIOD_MS[tf]))
        return out
    except (ValueError,KeyError,TypeError,OverflowError,IndexError) as exc:
        out.update(status='unavailable',reason=str(exc))
        return out


def resolve_anchor(anchor, parent_tf, rows, child_tf, as_of):
    """Unique exact extreme inside a fully covered native parent candle."""
    if anchor.get('kind') not in ('high','low') or PERIOD_MS[child_tf]>=PERIOD_MS[parent_tf]:
        raise ValueError('invalid_anchor_or_scale')
    start=anchor['open_time_ms']
    if anchor['confirmed_at_ms'] > time_ms(as_of):
        raise ValueError('parent_anchor_not_yet_known')
    end = start+PERIOD_MS[parent_tf]
    piece = [r for r in rows if start<=r['open_time_ms']<end]
    period = PERIOD_MS[child_tf]
    if (not piece or piece[0]['open_time_ms']!=start or piece[-1]['open_time_ms']+period!=end
            or len(piece)*period!=end-start):
        raise ValueError('parent_anchor_candle_not_fully_covered')
    key = 'high' if anchor['kind']=='high' else 'low'
    actual = max(r[key] for r in piece) if key=='high' else min(r[key] for r in piece)
    if actual!=anchor['price']:
        raise ValueError('parent_child_extreme_conflict')
    matches = [r for r in piece if r[key]==anchor['price']]
    if len(matches)!=1:
        raise ValueError('parent_extreme_ambiguous_or_missing')
    row = matches[0]
    child_anchor = dict(open_time_ms=row['open_time_ms'],kind=anchor['kind'],
                        price=anchor['price'],confirmed_at_ms=row['open_time_ms']+3*period)
    return child_anchor


def lower_evidence(parent, child_rows, child_tf, as_of):
    """Resolve a single parent extreme inside its native candle, without guessing.

    Timeframe is a source scale, not proof of wave degree. Repeated extreme
    touches / incomplete coverage / non-pivot child extremes stay unresolved.
    """
    out = dict(status='unavailable',timeframe=child_tf,wave_completion='unproven',probability=None)
    try:
        if parent.get('status')!='available':
            raise ValueError('parent_endpoint_unavailable')
        anchor = parent['endpoint'];start = anchor['open_time_ms']
        rows = closed_rows(child_rows,child_tf,as_of)
        child_anchor = resolve_anchor(anchor,parent['timeframe'],rows,child_tf,as_of)
        result = assess(rows,child_tf,as_of,child_anchor)
        result.update(parent_timeframe=parent['timeframe'],parent_anchor_at=iso(start),
                      shared_endpoint_price=anchor['price'],
                      parent_anchor_known_at=iso(anchor['confirmed_at_ms']))
        return result
    except (ValueError,KeyError,TypeError,OverflowError) as exc:
        out['reason']=str(exc)
        return out
