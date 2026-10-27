"""Experimental, opt-in Elliott observation ledger. No historical backfill or scheduler."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from scripts.elliott_candidates import build, hypothesis
from scripts.elliott_completion import closed_rows
from scripts.elliott_history import floor_time
from scripts.market_scenarios import iso, time_ms
from scripts.native_timeframe_candles import PERIOD_MS

MODEL = 'elliott_frozen_observation_v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def freeze(rows, tf, observed_at, source_state):
    """Create a point-in-time record; caller must supply independently checked source state.

    This primitive alone does not prove when it was run and MUST NOT be used for
    backfilling forecasts. Live persistence requires a separately reviewed runner.
    """
    if source_state != 'complete':
        raise ValueError('source_not_complete_or_conflicted')
    data = closed_rows(rows, tf, observed_at)
    inventory = build(data, tf, observed_at)
    if inventory['status'] != 'assessed' or inventory['scope'] != 'current_closed_window':
        raise ValueError('inventory_unavailable_or_historical')
    return dict(model_version=MODEL, market='bitget_btcusdt_usdt_futures',
                observed_at=observed_at, timeframe=tf, source_state=source_state,
                closed_through=inventory['closed_through'], rows=data,
                rows_sha256=digest(data), inventory=inventory,
                use='experimental_not_a_certified_forecast')


def evaluate(snapshot, later_rows, evaluated_at, source_state):
    """Re-evaluate the original anchors on each subsequent closed candle.

    Changed historical inputs, missing intervals and stale coverage are rejected.
    Only first rule violation is recorded, not a prediction hit or a win rate.
    """
    if source_state != 'complete' or snapshot.get('source_state') != 'complete':
        raise ValueError('source_not_complete_or_conflicted')
    if snapshot.get('model_version') != MODEL or digest(snapshot['rows']) != snapshot['rows_sha256']:
        raise ValueError('snapshot_invalid_or_tampered')
    tf = snapshot['timeframe']
    if time_ms(evaluated_at) <= time_ms(snapshot['observed_at']):
        raise ValueError('evaluation_not_later')
    rows = closed_rows(later_rows, tf, evaluated_at)
    old = snapshot['rows']
    if rows[:len(old)] != old:
        raise ValueError('original_source_revision_or_missing_history')
    if not rows or rows[-1]['open_time_ms'] + PERIOD_MS[tf] != floor_time(time_ms(evaluated_at),tf):
        raise ValueError('later_source_not_current')
    # Rebuild the original candidate inventory; caller-edited anchors cannot be trusted.
    original = build(old, tf, snapshot['observed_at'])
    if original != snapshot['inventory']:
        raise ValueError('snapshot_inventory_mismatch')
    results=[]
    for candidate in original['candidates']:
        result=dict(candidate_id=candidate['id'],initial_status=candidate['status'],
                    status='already_invalid' if candidate['status']=='invalid' else 'unresolved',
                    first_invalid_known_at=None,violated_rules=[])
        if candidate['status'] != 'invalid':
            for end in range(len(old)+1,len(rows)+1):
                current=hypothesis(rows[:end],candidate['points'],tf)
                broken=[c['rule'] for c in current['checks'] if c['result']=='geschonden']
                if broken:
                    result.update(status='invalidated',first_invalid_known_at=iso(rows[end-1]['open_time_ms']+PERIOD_MS[tf]),
                                  violated_rules=broken)
                    break
        results.append(result)
    return dict(model_version=MODEL, snapshot_sha256=digest(snapshot),evaluated_at=evaluated_at,
                source_rows_sha256=digest(rows),closed_through=iso(rows[-1]['open_time_ms']+PERIOD_MS[tf]),
                results=results,probability=None,wave_certification='unproven')


def save_immutable(directory, record):
    """Atomic create-only content-addressed record; never replace existing evidence."""
    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
    content=canonical(record)+'\n'; path=folder/(digest(record)+'.json'); tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=folder,delete=False) as f:
            tmp=Path(f.name);f.write(content)
        try:
            os.link(tmp,path)
        except FileExistsError:
            if path.read_text(encoding='utf-8') != content:
                raise ValueError('record_collision_or_tampering')
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return path
