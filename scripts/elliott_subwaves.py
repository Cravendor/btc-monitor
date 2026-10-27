"""Anchored one-level price subdivisions; no complete Elliott certification."""
from scripts.elliott_completion import closed_rows, resolve_anchor
from scripts.elliott_rules import confirmed_pivots, price_checks
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS
from scripts.elliott_history import reconcile

MODEL='elliott_anchored_subdivision_v2'


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


def correction_outlines(rows,points,direction):
    """Test independent endpoint geometries, never certify internal wave counts.

    Flat variants use strict B-origin/C-A relations from Waveopedia. Regular
    flats require an undefined 'near' relation and are intentionally not scored.
    """
    sign=1 if direction=='up' else -1
    p=[x['price']*sign for x in points]
    alternating=p[1]>p[0] and p[2]<p[1] and p[3]>p[2]
    # Any hidden excursion beyond an endpoint makes that fixed flat outline
    # unresolved. Do not replace anchors, tolerate wicks or thin extra pivots.
    contained=True
    for a,b in zip(points,points[1:]):
        part=[r for r in rows if a['open_time_ms']<r['open_time_ms']<b['open_time_ms']]
        lo,hi=sorted((a['price'],b['price']))
        if not part or any(r['low']<lo or r['high']>hi for r in part):
            contained=False
    variants=[dict(family='single_zigzag_outline',checks=zigzag_checks(rows,points,direction))]
    for family,endpoint in [('expanded_flat_outline',p[3]>p[1]),
                            ('running_flat_outline',p[2]<p[3]<p[1])]:
        conditions=[('ABC_richting',alternating),('B_voorbij_begin_A',p[2]<p[0]),
                    ('C_voorbij_A' if family=='expanded_flat_outline' else 'C_blijft_voor_A',endpoint),
                    ('vaste_eindpunten_alle_tussenliggende_wicks',contained)]
        checks=[dict(rule=k,result='getoetst' if ok else 'geschonden',
                     detail='Alleen geometrie tussen dezelfde bevestigde ankers; geen gecertificeerde flat.')
                for k,ok in conditions]
        checks.append(dict(rule='interne_A_B_C_3_3_5',result='niet toetsbaar',
                           detail='Interne 3-3-5 en context ontbreken; vooral running flats blijven een onbevestigde mogelijkheid.'))
        variants.append(dict(family=family,checks=checks))
    for v in variants:
        v['status']='price_outline_compatible' if not any(c['result']=='geschonden' for c in v['checks']) else 'unsupported_correction_outline'
    return variants


def _assess(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of,forming=False):
    out=dict(model_version=MODEL,status='unavailable',parent_timeframe=parent_tf,
             child_timeframe=child_tf,legs=[],wave_certification='unproven',probability=None)
    if forming:
        out.update(model_version='elliott_anchored_prefix_subdivision_v2',
                   ongoing_leg_status='unconfirmed_parent_endpoint_not_tested')
    if candidate.get('status')=='invalid':
        out.update(status='blocked_invalid_parent',reason='invalid_parent_not_rescued_by_children')
        return out
    try:
        if forming:
            from scripts.elliott_candidates import build as inventory
            if candidate.get('pattern')!='standard_impulse_prefix' or candidate.get('status')!='unresolved_price_prefix':
                raise ValueError('unsupported_prefix_family_or_state')
            # Rebuild the exact current suffix inventory, including ongoing wick
            # constraints. An ID or caller-supplied passing verdict alone is not
            # sufficient to accept fabricated, changed or obsolete anchors.
            current=inventory(parent_rows,parent_tf,as_of)
            actual=next((c for c in current['candidates'] if c['id']==candidate.get('id')),None)
            if actual is None or actual['points']!=candidate.get('points') or actual['direction']!=candidate.get('direction'):
                raise ValueError('prefix_not_in_as_of_inventory')
            points=actual['points'];direction=actual['direction'];checks=actual['checks']
            out.update(formed_legs=actual['completed_pivot_legs'],
                       ongoing_leg=actual['proposed_live_leg'],parent_scope=current['scope'])
        else:
            if candidate.get('status')!='provisional_price_pattern':
                raise ValueError('unsupported_parent_state')
            if candidate.get('pattern')!='standard_impulse':
                raise ValueError('unsupported_parent_family')
            points=candidate['points'];direction=candidate['direction']
        parents=closed_rows(parent_rows,parent_tf,as_of)
        children=closed_rows(child_rows,child_tf,as_of)
        if not forming:
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
            family='standard_impulse' if i%2 else 'corrective_outlines'
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
                if i%2:
                    tested=price_checks(children,selected,leg_direction)
                else:
                    alternatives=correction_outlines(children,selected,leg_direction)
                    leg['correction_alternatives']=alternatives
                    leg['compatible_families']=[v['family'] for v in alternatives if v['status']=='price_outline_compatible']
                    tested=[dict(c,rule=v['family']+' · '+c['rule']) for v in alternatives for c in v['checks']]
                # A rejected alternative does not invalidate a different matching
                # geometry; all alternatives and their failures remain visible.
                leg['checks']=tested
                if (any(c['result']=='geschonden' for c in tested) if i%2 else not leg['compatible_families']):
                    leg['status']='price_rules_violated' if i%2 else 'unsupported_correction_outline'
                else:
                    leg['status']='price_outline_compatible'
                leg['evidence_known_at']=iso(max(b['confirmed_at_ms'],right['confirmed_at_ms']))
            except (ValueError,KeyError,TypeError,OverflowError) as exc:
                leg['reason']=str(exc)
        out['compatible_legs']=sum(l['status']=='price_outline_compatible' for l in out['legs'])
        out['price_subdivision_status']='compatible_outlines' if out['compatible_legs']==len(points)-1 else 'incomplete_or_rejected'
        return out
    except (ValueError,KeyError,TypeError,OverflowError,IndexError) as exc:
        out.update(status='unavailable',reason=str(exc))
        return out


def assess(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of):
    """A supplied completed standard-impulse outline; original contract."""
    return _assess(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of)


def assess_prefix(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of):
    """Only confirmed legs of an exact as-of forming prefix, with shared anchors.

    The next ongoing leg has no confirmed parent endpoint and stays untested.
    Price-outline compatibility never establishes wave degree or certification.
    """
    return _assess(candidate,parent_rows,parent_tf,child_rows,child_tf,as_of,forming=True)
