"""Recover only pre-archive signals already stored in dated Bitget snapshots.

No API calls, candle replay or model recomputation. Existing observations are
never edited or enriched retrospectively. A one-minute boundary margin avoids
duplicating the first live row whose feed timestamp follows snapshot finish.
"""
import json
from datetime import timedelta
from pathlib import Path
from scripts.history_coverage import observations
from scripts.signal_outcome_validation import parse_time
from scripts.timeframe_signal_history import TIMEFRAMES, GRADES


def recover(snapshot, source, before):
    if not isinstance(snapshot, dict) or any(snapshot.get(k) != v for k, v in
        {'exchange': 'bitget', 'market': 'USDT-FUTURES', 'symbol': 'BTCUSDT'}.items()):
        return None
    stamp = parse_time(snapshot.get('finished_at'))
    started = parse_time(snapshot.get('started_at'))
    if not stamp or not started or stamp < started or stamp >= before - timedelta(minutes=1):
        return None
    native = ((snapshot.get('metrics') or {}).get('multi_timeframe') or {}).get('data')
    if not isinstance(native, dict):
        return None
    signals = {}
    for tf in TIMEFRAMES:
        metric = native.get(tf) or {}
        signal = metric.get('signal') or {}
        closed = parse_time(signal.get('observed_at'))
        model = signal.get('model_version')
        ok = (metric.get('status') == 'ok' and signal.get('status') == 'provisional'
              and signal.get('grade') in GRADES and closed is not None and closed <= stamp
              and isinstance(model, str) and bool(model))
        # Close prices are deliberately not recovered: matching historical
        # price/candle integrity needs separate validation. Outcomes stay pending.
        signals[tf] = {'status': 'ok' if ok else 'unavailable',
                       'grade': signal.get('grade') if ok else None,
                       'candle_closed_at': closed.isoformat() if ok else None,
                       'model_version': model if ok else None, 'close_price': None}
    return {'updated_at': stamp.isoformat(), 'signals': signals,
            'provenance': {'kind': 'recovered_stored_signal', 'source': source,
                           'timestamp_basis': 'snapshot.finished_at',
                           'note': 'Original stored labels; no model replay or recovered outcome prices.'}}


def run(root='data', archive='data/history/timeframe_signals.jsonl'):
    target = Path(archive)
    lines = target.read_text(encoding='utf-8').splitlines() if target.exists() else []
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    existing = observations(records)
    if not existing:
        raise ValueError('An existing live archive boundary is required')
    # Keep the original live boundary stable on repeated recovery runs.
    live = [(t, r) for t, r in existing if not r.get('provenance')]
    if not live:
        raise ValueError('No live archive boundary')
    before = live[0][0]
    seen = {t for t, _ in existing}
    recovered = []
    for path in sorted(Path(root).glob('????/??/??/*.json')):
        try:
            row = recover(json.loads(path.read_text(encoding='utf-8')),
                          path.relative_to(Path(root)).as_posix(), before)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if row and parse_time(row['updated_at']) not in seen:
            recovered.append(row)
            seen.add(parse_time(row['updated_at']))
    if recovered:
        with target.open('a', encoding='utf-8') as handle:
            if lines and not target.read_text(encoding='utf-8').endswith('\n'):
                handle.write('\n')
            for row in recovered:
                handle.write(json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n')
    return {'recovered_observations': len(recovered), 'live_boundary': before.isoformat()}


if __name__ == '__main__':
    print(json.dumps(run()))
