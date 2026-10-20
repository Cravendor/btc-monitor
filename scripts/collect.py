"""Public Bitget USDT futures snapshots. Python standard library only; no credentials."""
import json
import os
import socket
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = 'https://api.bitget.com/api/v2/mix/market/ticker?symbol=BTCUSDT&productType=USDT-FUTURES'
ENDPOINTS = {
    'futures_price': (URL, ['lastPr'], ['ts']),
    'open_interest': (URL, ['holdingAmount'], ['ts']),
    'funding': (URL, ['fundingRate'], ['ts']),
}


def utcnow():
    return datetime.now(timezone.utc)


def fetch(url, numbers, timestamps, opener=urlopen, sleep=time.sleep):
    result = {'url': url, 'status': 'error', 'data': None, 'error': None}
    for attempt in range(1, 4):
        result.update(attempts=attempt, observed_at=utcnow().isoformat())
        try:
            with opener(Request(url, headers={'User-Agent': 'btc-public-monitor/1.0'}), timeout=20) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise ValueError('Unexpected response format')
            if payload.get('code') != '00000':
                result['error'] = {'kind': 'api', 'code': payload.get('code')}
                return result
            rows = payload.get('data')
            if not isinstance(rows, list):
                raise ValueError('Expected ticker list')
            payload = next((row for row in rows if isinstance(row, dict) and row.get('symbol') == 'BTCUSDT'), None)
            if payload is None:
                result.update(status='missing_data', error={'kind': 'missing_symbol'})
                return result
            missing = [k for k in numbers + timestamps if payload.get(k) in (None, '')]
            if missing:
                result.update(status='missing_data', error={'kind': 'missing_fields', 'fields': missing})
                return result
            for key in numbers:
                value = Decimal(str(payload[key]))
                if not value.is_finite() or (key != 'fundingRate' and value < 0):
                    raise ValueError('Invalid numeric field: ' + key)
            for key in timestamps:
                if not str(payload[key]).isdigit() or int(payload[key]) <= 0:
                    raise ValueError('Invalid timestamp: ' + key)
            result.update(status='ok', data=payload, error=None)
            return result
        except HTTPError as exc:
            result['error'] = {'kind': 'http', 'http_status': exc.code}
            # Do not bypass regional restrictions or repeatedly hit rate limits.
            if exc.code < 500:
                return result
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            result['error'] = {'kind': 'network', 'type': type(exc).__name__}
        except (ValueError, InvalidOperation, TypeError) as exc:
            result['error'] = {'kind': 'invalid_data', 'message': str(exc)[:200]}
            return result
        if attempt < 3:
            sleep(2 ** attempt)
    return result


def main():
    started = utcnow()
    metrics = {name: fetch(*spec) for name, spec in ENDPOINTS.items()}
    successes = sum(item['status'] == 'ok' for item in metrics.values())
    status = 'ok' if successes == len(metrics) else ('partial' if successes else 'error')
    record = {
        'schema_version': 2, 'exchange': 'bitget', 'market': 'USDT-FUTURES', 'symbol': 'BTCUSDT', 'started_at': started.isoformat(),
        'finished_at': utcnow().isoformat(), 'status': status, 'metrics': metrics,
        'cvd_4h': {'status': 'not_collected', 'value': None,
                   'reason': 'Requires complete trade coverage of the full 4h interval; five aggTrades are insufficient.'},
    }
    run = os.environ.get('GITHUB_RUN_ID', 'local')
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    destination = Path('data') / started.strftime('%Y/%m/%d')
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / (started.strftime('%Y%m%dT%H%M%S%fZ') + f'-{run}-{attempt}.json')
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    # Fixed public URL with recent snapshots; dated files remain the archive.
    recent_paths = sorted(Path('data').glob('????/??/??/*.json'), reverse=True)
    measurements = []
    for recent_path in recent_paths:
        try:
            item = json.loads(recent_path.read_text())
        except (OSError, ValueError):
            continue
        if (item.get('schema_version') == 2 and item.get('exchange') == 'bitget'
                and item.get('market') == 'USDT-FUTURES' and item.get('symbol') == 'BTCUSDT'):
            measurements.append(item)
        if len(measurements) == 14:
            break
    feed = {
        'feed_schema_version': 1,
        'updated_at': utcnow().isoformat(),
        'exchange': 'bitget',
        'market': 'USDT-FUTURES',
        'symbol': 'BTCUSDT',
        'order': 'newest_first',
        'measurements': measurements,
    }
    feed_path = Path('data/latest.json')
    temporary = feed_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(feed, indent=2, allow_nan=False) + '\n')
    temporary.replace(feed_path)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as handle:
            handle.write(f'Bitget BTCUSDT futures: **{status}**\n\n')
            for name, metric in metrics.items():
                handle.write(f'- {name}: {metric["status"]}\n')
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a') as handle:
            handle.write(f'status={status}\n')
    print(f'{path}: {status}')


if __name__ == '__main__':
    main()
