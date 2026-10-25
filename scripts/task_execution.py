"""Strict, privacy-minimal execution receipts. Missing receipts never prove failure."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

TASKS = {
    ('chatgpt', '4h-warning'): ('BTC 4H en dagrapport', 6 * 3600),
    ('chatgpt', 'psychology'): ('BTC psychologie en scenario’s', 30 * 3600),
    ('chatgpt', 'breaking-risk'): ('Breaking Market Risk Alert', 3 * 3600),
    ('chatgpt', 'quality-improvement'): ('BTC Quality & Improvement', 35 * 86400),
    ('nas', 'watchdog'): ('BTC CVD Watchdog', 45 * 60),
    ('nas', 'storage'): ('CVD-opslagcontrole', 36 * 3600),
    ('nas', 'startup'): ('CVD-opstarttaak', None),
}
FIELDS = {'schema_version', 'source', 'task', 'started_at', 'finished_at', 'outcome'}


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp required')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('timezone required')
    return dt.astimezone(timezone.utc)


def validate(value, path=None):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('invalid receipt fields')
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError('invalid schema')
    key = (value['source'], value['task'])
    if key not in TASKS or value['outcome'] not in ('completed', 'error'):
        raise ValueError('invalid identity or outcome')
    finish = stamp(value['finished_at'])
    if value['started_at'] is not None and stamp(value['started_at']) > finish:
        raise ValueError('reversed interval')
    if path is not None:
        expected = Path(*key, finish.strftime('%Y%m%dT%H%M%SZ') + '.json')
        if Path(path) != expected:
            raise ValueError('receipt path mismatch')
    return finish


def read_items(root, as_of):
    now = stamp(as_of)
    root = Path(root)
    rows = []
    for (source, task), (name, seconds) in TASKS.items():
        candidates = []
        # Filename identity is the immutable completion time. A newer malformed
        # record must not reveal an older green success instead.
        for path in (root / source / task).glob('*.json'):
            try:
                key = datetime.strptime(path.stem, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            except ValueError:
                candidates.append((datetime.max.replace(tzinfo=timezone.utc), path))
            else:
                candidates.append((key, path))
        row = dict(id='task-' + source + '-' + task, name=name, system=source.upper() + ' / uitvoerbewijs',
                   state='unknown', label='Nog geen uitvoerbewijs', evidence_at=None, expires_at=None,
                   detail='Dit bewijs toont een voltooide controle, geen live processtatus, datakwaliteit of aflevering van meldingen.')
        if candidates:
            path = max(candidates, key=lambda pair: pair[0])[1]
            try:
                value = json.loads(path.read_text())
                finish = validate(value, path.relative_to(root))
                if finish > now:
                    raise ValueError('future receipt')
                row['evidence_at'] = value['finished_at']
                if value['outcome'] == 'error':
                    row.update(state='error', label='Laatste controle mislukt')
                elif seconds is None:
                    row.update(label='Opstartuitvoering vastgelegd', detail='Een opstarttaak draait alleen bij opstart. Dit bewijst geen huidige processtatus.')
                else:
                    from datetime import timedelta
                    expiry = finish + timedelta(seconds=seconds)
                    row.update(state='good' if now <= expiry else 'attention',
                               label='Controle uitgevoerd' if now <= expiry else 'Uitvoerbewijs verouderd',
                               expires_at=expiry.isoformat())
            except (ValueError, TypeError, KeyError, OSError, OverflowError):
                row.update(label='Ongeldig uitvoerbewijs')
        rows.append(row)
    return rows


def write_receipt(root, task, outcome, started_at=None):
    finish = datetime.now(timezone.utc)
    value = dict(schema_version=1, source='nas', task=task, started_at=started_at,
                 finished_at=finish.isoformat(), outcome=outcome)
    validate(value)
    path = Path(root) / 'nas' / task / (finish.strftime('%Y%m%dT%H%M%SZ') + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never replace even a colliding same-second receipt.
    with path.open('x') as output:
        output.write(json.dumps(value, allow_nan=False) + '\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=['watchdog', 'storage', 'startup'])
    parser.add_argument('outcome', choices=['completed', 'error'])
    parser.add_argument('--root', default='data/task-executions')
    parser.add_argument('--started-at')
    args = parser.parse_args()
    write_receipt(args.root, args.task, args.outcome, args.started_at)
