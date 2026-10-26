"""Anchored one-level price subdivisions; no complete Elliott certification."""
from scripts.elliott_completion import closed_rows, resolve_anchor
from scripts.elliott_rules import confirmed_pivots, price_checks
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS
from scripts.elliott_history import reconcile

MODEL='elliott_anchored_subdivision_v1'


def same(a,b):
    return all(a[k]==b[k] for k in ('open_time_ms','kind','price','confirmed_at_ms'))


def zigzag_checks(rows,points,direction):
    """Conservative, non-truncated single-zigzag price outline only.

    Other corrective families are unsupported, not universally invalidated by
    these conditions. Internal A/B/C 5-3-5 subdivisions remain untested.
    """
    sign=1 if direction=='up' else -1
    p=[x['price']*sign for x in points]
    middle=[r['low'] if sign==1 else -r['high'] for r in rows
            if points[1]['open_time_ms']<r['open_time_ms']<=points[2]['open_time_ms']]
    conditions=[('ABC_richting',p[1]>p[0] and p[2]<p[1] and p[3]>p[2]),
                ('B_strikt_binnen_A',p[0]<p[2]<p[1] and bool(middle) and min(middle)>p[0]),
                ('C_voorbij_A_beperkte_familie',p[3]>p[1])]
    return [dict(rule=k,result='getoetst' if ok else 'geschonden',
                 detail='Alleen deze beperkte zigzag-prijsvorm; geen uitspraak over andere correcties.')
            for k,ok in conditions]+[dict(rule='interne_A_B_C_5_3_5',result='niet toetsbaar',
                                         detail='Vereist nog een lagere gevalideerde golfgraad.')]


def assess(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of):
    out=dict(model_version=MODEL,status='unavailable',parent_timeframe=parent_tf,
             child_timeframe=child_tf,legs=[],wave_certification='unproven',probability=None)
    if candidate.get('status')=='invalid':
        out.update(status='blocked_invalid_parent',reason='invalid_parent_not_rescued_by_children')
        return out
    try:
        if candidate.get('status')!='provisional_price_pattern':
            raise ValueError('unsupported_parent_state')
        if candidate.get('pattern')!='standard_impulse':
            raise ValueError('unsupported_parent_family')
        parents=closed_rows(parent_rows,parent_tf,as_of)
        children=closed_rows(child_rows,child_tf,as_of)
        points=candidate['points'];direction=candidate['direction']
        checks=price_checks(parents,points,direction)
        if any(c['result']=='geschonden' for c in checks):
            out.update(status='blocked_invalid_parent',reason='recomputed_parent_rules_violated')
            return out
        for anchor in points:
            prefix=[r for r in parents if r['open_time_ms']+PERIOD_MS[parent_tf]<=anchor['confirmed_at_ms']]
            if anchor['confirmed_at_ms']>time_ms(as_of) or not any(same(p,anchor) for p in confirmed_pivots(prefix)):
                raise ValueError('parent_pivot_not_known_at_as_of')
        span=[r for r in parents if points[0]['open_time_ms']<=r['open_time_ms']<=points[-1]['open_time_ms']]
        review=reconcile({r['open_time_ms']:r for r in children},span,child_tf,parent_tf)
        if review['mismatch_candles'] or review['skipped_incomplete_groups']:
            raise ValueError('parent_child_source_conflict_or_missing_group')
        out.update(status='assessed',evidence_known_at=iso(max(p['confirmed_at_ms'] for p in points)))
        for i,(a,b) in enumerate(zip(points,points[1:]),1):
            family='standard_impulse' if i%2 else 'single_zigzag_outline'
            leg_direction=direction if i%2 else ('down' if direction=='up' else 'up')
            leg=dict(leg=i,family=family,direction=leg_direction,status='unresolved',
                     start_price=a['price'],end_price=b['price'],points=[],checks=[])
            out['legs'].append(leg)
            try:
                left=resolve_anchor(a,parent_tf,children,child_tf,as_of)
                right=resolve_anchor(b,parent_tf,children,child_tf,as_of)
                if left['open_time_ms']>=right['open_time_ms']:
                    raise ValueError('ambiguous_anchor_order')
                # Freeze selection when the mapped end pivot became knowable.
                # Never skip extra pivots until an attractive five/three remains.
                prefix=[r for r in children if r['open_time_ms']+PERIOD_MS[child_tf]<=right['confirmed_at_ms']]
                pivots=confirmed_pivots(prefix)
                selected=[p for p in pivots if left['open_time_ms']<=p['open_time_ms']<=right['open_time_ms']]
                if not selected or not same(selected[0],left) or not same(selected[-1],right):
                    raise ValueError('mapped_anchors_not_confirmed_child_pivots')
                expected=6 if i%2 else 4
                leg.update(points=selected,observed_legs=len(selected)-1,expected_legs=expected-1,
                           mapped_start_at=iso(left['open_time_ms']),mapped_end_at=iso(right['open_time_ms']))
                if len(selected)!=expected:
                    raise ValueError('different_or_unresolved_child_degree')
                tested=price_checks(children,selected,leg_direction) if i%2 else zigzag_checks(children,selected,leg_direction)
                leg['checks']=tested
                if any(c['result']=='geschonden' for c in tested):
                    leg['status']='price_rules_violated' if i%2 else 'unsupported_correction_outline'
                else:
                    leg['status']='price_outline_compatible'
                leg['evidence_known_at']=iso(max(b['confirmed_at_ms'],right['confirmed_at_ms']))
            except (ValueError,KeyError,TypeError,OverflowError) as exc:
                leg['reason']=str(exc)
        out['compatible_legs']=sum(l['status']=='price_outline_compatible' for l in out['legs'])
        out['price_subdivision_status']='compatible_outlines' if out['compatible_legs']==5 else 'incomplete_or_rejected'
        return out
    except (ValueError,KeyError,TypeError,OverflowError,IndexError) as exc:
        out.update(status='unavailable',reason=str(exc))
        return out
