"""Archive original monitor text; extract only explicitly printed bias scores.

Inbox files are untrusted data, never commands or evidence that market claims
are true. Existing dated records are immutable; conflicting submissions remain
rejected rather than replacing history.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

MONITORS = {'daily', '4h-warning', 'market-risk', 'psychology'}
HORIZONS = ('4h_1d', '7d', '30d_macro')
LABELS = {-2: 'STERK BEARISH', -1: 'ZWAK BEARISH', 0: 'NEUTRAAL/GEMENGD',
          1: 'ZWAK BULLISH', 2: 'STERK BULLISH'}
MAX_TEXT = 60000


def timestamp(value, now=None):
    if not isinstance(value, str):
        raise ValueError('Invalid report timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Report timezone required')
    parsed = parsed.astimezone(timezone.utc)
    if parsed.year < 2020 or parsed > (now or datetime.now(timezone.utc)) + timedelta(minutes=10):
        raise ValueError('Report timestamp outside accepted range')
    return parsed


def checksum(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_bias(text):
    matches = {h: [] for h in HORIZONS}
    for original in text.splitlines():
        line = original.replace('**', '').replace('`', '').replace('−', '-').strip()
        line = re.sub(r'^[#*\- ]+', '', line)
        if line.startswith('|'):
            cells = [x.strip() for x in line.strip('|').split('|')]
            if len(cells) >= 2:
                line = cells[0] + ': ' + cells[1]
        match = re.match(r'^(4H[–—-]1D|7D|30D/macro)\s*:\s*(.+)$', line, re.I)
        if not match:
            continue
        horizon = ('4h_1d' if re.match('4H', match[1], re.I) else
                   '7d' if match[1].upper() == '7D' else '30d_macro')
        value = match[2].strip()
        entry = None
        if re.match(r'^ONVOLDOENDE DATA(?:\s|$)', value, re.I):
            entry = {'score': None, 'status': 'ONVOLDOENDE DATA', 'reason': original.strip()}
        else:
            score = re.match(r'^(-2|-1|0|\+?1|\+?2)\s+(STERK BEARISH|ZWAK BEARISH|NEUTRAAL(?:/GEMENGD)?|ZWAK BULLISH|STERK BULLISH)(?=\s|$)', value, re.I)
            if score:
                numeric = int(score[1])
                label = score[2].upper()
                if label == LABELS[numeric] or (numeric == 0 and label == 'NEUTRAAL'):
                    entry = {'score': numeric, 'status': 'REPORTED', 'reason': original.strip()}
        if entry:
            matches[horizon].append(entry)
    output = {}
    for horizon, entries in matches.items():
        distinct = {(e['score'], e['status']) for e in entries}
        output[horizon] = (entries[0] if len(distinct) == 1 else
                           {'score': None, 'status': 'NOT_REPORTED',
                            'reason': 'Tegenstrijdige expliciete scores.' if entries else
                                      'Geen expliciete vijfpuntsscore voor deze horizon aangetroffen.'})
    return output


def validate_submission(obj, now=None):
    if (not isinstance(obj, dict) or set(obj) !=
            {'schema_version', 'monitor', 'reported_at', 'report_text', 'source'} or
            type(obj['schema_version']) is not int or obj['schema_version'] != 2):
        raise ValueError('Unsupported submission schema')
    if obj['monitor'] not in MONITORS or obj['source'] != 'chatgpt_monitor':
        raise ValueError('Unknown report source or monitor')
    text = obj['report_text']
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT or '\x00' in text:
        raise ValueError('Invalid or oversized report text')
    return timestamp(obj['reported_at'], now)


def validate_record(obj, now=None):
    original = {k: v for k, v in obj.items() if k not in ('bias', 'content_sha256')}
    ts = validate_submission(original, now)
    if (obj.get('content_sha256') != checksum(obj['report_text']) or
            obj.get('bias') != extract_bias(obj['report_text'])):
        raise ValueError('Stored report text, digest or scores disagree')
    return ts


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(raw, encoding='utf-8')
    temporary.replace(path)


def import_inbox(root='.', now=None):
    root = Path(root)
    reports = root / 'reports'
    rejected = []
    imported = 0
    for path in sorted((reports / 'inbox').glob('*/*.json')):
        try:
            if path.is_symlink() or path.stat().st_size > MAX_TEXT * 6 + 4096:
                raise ValueError('Invalid submission file')
            raw = json.loads(path.read_text(encoding='utf-8'))
            ts = validate_submission(raw, now)
            if (path.parent.name != raw['monitor'] or
                    path.name != ts.strftime('%Y%m%dT%H%M%SZ.json')):
                raise ValueError('Inbox path and report identity disagree')
            target = reports / ts.strftime('%Y/%m/%d') / (raw['monitor'] + '-' + ts.strftime('%H%M%S') + '.json')
            record = dict(raw, bias=extract_bias(raw['report_text']), content_sha256=checksum(raw['report_text']))
            if target.exists():
                if target.is_symlink() or json.loads(target.read_text(encoding='utf-8')) != record:
                    raise ValueError('Existing report conflicts; history preserved')
            else:
                write_json(target, record)
                imported += 1
        except (ValueError, TypeError, OSError, UnicodeError, KeyError):
            rejected.append({'path': str(path.relative_to(root)), 'reason': 'Submission rejected; existing history preserved.'})
    # Validate every index entry, including legacy manually submitted reports.
    if __package__:
        from .archive_report import validate
    else:
        from archive_report import validate
    index = []
    for path in sorted(reports.glob('20??/??/??/*.json')):
        try:
            if path.is_symlink():
                raise ValueError('Symlink report')
            record = json.loads(path.read_text(encoding='utf-8'))
            validate(record)
            ts = timestamp(record['reported_at'], now)
            expected = reports / ts.strftime('%Y/%m/%d') / (record['monitor'] + '-' + ts.strftime('%H%M%S') + '.json')
            if path != expected:
                raise ValueError('Archive path and identity disagree')
            index.append({'path': str(path.relative_to(root)), 'monitor': record['monitor'],
                          'reported_at': record['reported_at'], 'bias': record['bias'],
                          'has_report_text': bool(record.get('report_text')),
                          'content_sha256': record.get('content_sha256')})
        except (ValueError, TypeError, OSError, UnicodeError, KeyError):
            rejected.append({'path': str(path.relative_to(root)), 'reason': 'Invalid stored report excluded from index.'})
    write_json(reports / 'index.json', {'schema_version': 2, 'reports': index,
                                      'rejected_count': len(rejected), 'rejected': rejected})
    return {'imported': imported, 'indexed': len(index), 'rejected': len(rejected)}


if __name__ == '__main__':
    print(json.dumps(import_inbox()))
