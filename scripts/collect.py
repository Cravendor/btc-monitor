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
try:
    from .enrich import collect_extra
    from .cvd_export import collect_cvd
except ImportError:
    from enrich import collect_extra
    from cvd_export import collect_cvd

URL = 'https://api.bitget.com/api/v2/mix/market/ticker?symbol=BTCUSDT&productType=USDT-FUTURES'
ENDPOINTS = {
    'futures_price': (URL, ['lastPr'], ['ts']),
    'open_interest': (URL, ['holdingAmount'], ['ts']),
    'funding': (URL, ['fundingRate'], ['ts']),
}


def utcnow():
    return datetime.now(timezone.utc)


def collection_source():
    source = os.environ.get('BTC_COLLECTOR_SOURCE')
    if source in ('nas', 'github_fallback', 'github_manual', 'local'):
        return source
    return 'github_manual' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'local'


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
    metrics.update(collect_extra(metrics))
    # Native timeframes are optional context; per-timeframe failures stay explicit.
    try:
        from scripts.multi_timeframe_collector import collect_native_timeframes
    except ImportError:
        from multi_timeframe_collector import collect_native_timeframes
    native = collect_native_timeframes()
    metrics['multi_timeframe'] = {
        'status': 'ok', 'data': native,
        'observed_at': utcnow().isoformat(),
        'scope': 'Individual timeframe statuses are authoritative.'}

    successes = sum(item['status'] == 'ok' for item in metrics.values())
    status = 'ok' if successes == len(metrics) else ('partial' if successes else 'error')
    record = {
        'collection_source': collection_source(),
        'schema_version': 2, 'exchange': 'bitget', 'market': 'USDT-FUTURES', 'symbol': 'BTCUSDT', 'started_at': started.isoformat(),
        'finished_at': utcnow().isoformat(), 'status': status, 'metrics': metrics,
        # Optional CVD observations have their own status; market ok never attests CVD.
        'cvd_4h': collect_cvd(now=started),
    }
    # Preserve original scenario routes and level checks, never user positions.
    try:
        from scripts.scenario_archive import freeze
    except ModuleNotFoundError:
        from scenario_archive import freeze
    try:
        from scripts.cycle_history import reference as history_reference, PATH as history_path
    except ImportError:
        from cycle_history import reference as history_reference, PATH as history_path
    record['cycle_history_reference']=history_reference(history_path,record['finished_at'])
    record['scenario_snapshot'] = freeze(record)
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
    # Compact machine-readable health report, avoiding large latest.json fetches.
    health = {
        'schema_version': 1,
        'updated_at': feed['updated_at'],
        'exchange': 'bitget',
        'market': 'USDT-FUTURES',
        'symbol': 'BTCUSDT',
        'snapshot_status': status,
        'timeframes': {},
    }
    for tf, metric in native.items():
        signal = metric.get('signal') or {}
        candle_data = metric.get('data')
        candles = candle_data.get('candles') if isinstance(candle_data, dict) else None
        health['timeframes'][tf] = {
            'status': metric.get('status', 'missing_data'),
            'signal_status': signal.get('status', 'unavailable'),
            'grade': signal.get('grade') if signal.get('status') == 'provisional' else None,
            'confidence': signal.get('confidence') if signal.get('status') == 'provisional' else None,
            'evidence_state': (signal.get('evidence') or {}).get('state') if signal.get('status') == 'provisional' else None,
            'model_version': signal.get('model_version') if signal.get('status') == 'provisional' else None,
            'candle_close_price': (candles[-1].get('close') if candles and signal.get('status') == 'provisional' else None),
            'closed_candles': len(candles) if isinstance(candles, list) else None,
            'observed_at': signal.get('observed_at') or metric.get('observed_at'),
            'error': metric.get('error') or signal.get('reason'),
        }
    health_path = Path('data/timeframe-health.json')
    health_path.write_text(json.dumps(health, indent=2, allow_nan=False) + '\n')
    try:
        from scripts.timeframe_signal_history import record_health
    except ImportError:
        from timeframe_signal_history import record_health
    record_health(health)
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

