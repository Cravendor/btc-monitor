"""Bounded public Bitget history recovery into a SEPARATE local candidate store.

No live journal writes, gap resolution, validated CVD or automatic activation.
Python 3.8+. One closed UTC 4H interval and one market per invocation.
"""
import argparse
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import socket
import ssl
import os
from pathlib import Path
import sqlite3
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import uuid

WINDOW = 14400000
PATHS = {'spot': '/api/v2/spot/market/', 'usdt_futures': '/api/v2/mix/market/'}
SCHEMA = '''
CREATE TABLE IF NOT EXISTS cvd_backfill_runs(
 run_id TEXT PRIMARY KEY,market TEXT NOT NULL,start_ms INTEGER NOT NULL,
 end_ms INTEGER NOT NULL,report_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cvd_backfill_pages(
 run_id TEXT NOT NULL,page_no INTEGER NOT NULL,cursor TEXT,next_cursor TEXT,
 row_count INTEGER NOT NULL,response_sha256 TEXT NOT NULL,payload_json TEXT NOT NULL,
 PRIMARY KEY(run_id,page_no));
CREATE TABLE IF NOT EXISTS cvd_backfill_trades(
 run_id TEXT NOT NULL,trade_id TEXT NOT NULL,ts_ms INTEGER NOT NULL,
 price TEXT NOT NULL,size_btc TEXT NOT NULL,side TEXT NOT NULL,page_no INTEGER NOT NULL,
 PRIMARY KEY(run_id,trade_id));
CREATE INDEX IF NOT EXISTS cvd_backfill_page_rows
 ON cvd_backfill_trades(run_id,page_no);
'''


class AuditError(ValueError):
    pass


def integer(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and 0 < len(value) <= 24 and value.isascii() and value.isdecimal():
        return int(value)
    raise AuditError('invalid_integer')


def decimal(value, zero=False):
    if not isinstance(value, str) or len(value) > 80:
        raise AuditError('invalid_decimal')
    try:
        number = Decimal(value)
        if (not number.is_finite() or number < 0 or (not zero and number == 0) or
                len(number.as_tuple().digits) > 30 or
                not -30 <= number.as_tuple().exponent <= 10):
            raise AuditError('invalid_decimal')
    except InvalidOperation:
        raise AuditError('invalid_decimal')
    return number


def request(path, params, timeout):
    # Fixed origin/path allowlist; no keys, redirects to arbitrary hosts or retries.
    if path not in [base + suffix for base in PATHS.values()
                    for suffix in ('fills-history', 'history-candles')]:
        raise AuditError('unexpected_endpoint')
    from urllib.request import HTTPRedirectHandler, build_opener

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    url = 'https://api.bitget.com' + path + '?' + urlencode(params)
    with build_opener(NoRedirect).open(url, timeout=timeout) as response:
        payload = response.read(1048577)
    if len(payload) > 1048576:
        raise AuditError('response_too_large')
    obj = json.loads(payload)
    if not isinstance(obj, dict) or obj.get('code') != '00000' or not isinstance(obj.get('data'), list):
        raise AuditError('invalid_api_response')
    return obj


def open_store(output, journal):
    output, journal = Path(output).resolve(), Path(journal).resolve()
    repo = Path(__file__).resolve().parents[1]
    if output == repo or repo in output.parents:
        raise AuditError('candidate_store_must_be_outside_repository')
    if output == journal or (output.exists() and journal.exists() and os.path.samefile(output, journal)):
        raise AuditError('candidate_store_must_differ_from_journal')
    if not journal.is_file():
        raise AuditError('journal_missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(output.as_uri() + '?mode=rwc', uri=True, timeout=10)
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables & {'trades', 'gaps', 'cvd_sessions'}:
            raise AuditError('refusing_live_journal_as_candidate_store')
        db.executescript(SCHEMA)
        db.execute('ATTACH DATABASE ? AS journal', (journal.as_uri() + '?mode=ro',))
        db.execute('SELECT market,trade_id,ts_ms,price,size_btc,taker_side FROM journal.trades LIMIT 0')
    except Exception:
        db.close()
        raise
    return db


def parse_rows(rows, run_id, page_no, cursor, start, end):
    if not isinstance(rows, list) or len(rows) > 1000:
        raise AuditError('oversized_or_invalid_page')
    parsed = []
    previous_id = integer(cursor) if cursor is not None else None
    for row in rows:
        if not isinstance(row, dict) or row.get('symbol') != 'BTCUSDT':
            raise AuditError('wrong_trade_identity')
        ident = row.get('tradeId')
        if not isinstance(ident, str) or str(integer(ident)) != ident:
            raise AuditError('invalid_trade_id')
        if previous_id is not None and integer(ident) >= previous_id:
            raise AuditError('cursor_or_order_violation')
        previous_id = integer(ident)
        ts = integer(row.get('ts'))
        if not start <= ts < end:
            raise AuditError('trade_outside_interval')
        side = row.get('side')
        if not isinstance(side, str) or side.lower() not in ('buy', 'sell'):
            raise AuditError('invalid_trade_side')
        decimal(row.get('price'))
        decimal(row.get('size'))
        parsed.append((run_id, ident, ts, row['price'], row['size'], side.lower(), page_no))
    return parsed


def resume_checkpoint(db, run_id, start, end):
    """Derive progress from durable page transactions, never from report counters."""
    cursor, count, pages, exhausted = None, 0, 0, False
    for number, old_cursor, next_cursor, row_count, digest, payload in db.execute(
            'SELECT page_no,cursor,next_cursor,row_count,response_sha256,payload_json '
            'FROM cvd_backfill_pages WHERE run_id=? ORDER BY page_no', (run_id,)):
        if exhausted or number != pages + 1 or old_cursor != cursor:
            raise AuditError('resume_page_chain_invalid')
        if hashlib.sha256(payload.encode()).hexdigest() != digest:
            raise AuditError('resume_payload_hash_mismatch')
        obj = json.loads(payload)
        if not isinstance(obj, dict) or obj.get('code') != '00000':
            raise AuditError('resume_payload_invalid')
        parsed = parse_rows(obj.get('data'), run_id, number, cursor, start, end)
        expected_cursor = parsed[-1][1] if parsed else None
        if row_count != len(parsed) or next_cursor != expected_cursor:
            raise AuditError('resume_page_metadata_mismatch')
        saved = db.execute('SELECT * FROM cvd_backfill_trades WHERE run_id=? AND page_no=? '
                           'ORDER BY trade_id', (run_id, number)).fetchall()
        if saved != sorted(parsed, key=lambda r: r[1]):
            raise AuditError('resume_trade_payload_mismatch')
        cursor, pages, count = next_cursor, number, count + len(parsed)
        exhausted = not parsed
    actual = db.execute('SELECT COUNT(*) FROM cvd_backfill_trades WHERE run_id=?',
                        (run_id,)).fetchone()[0]
    if count != actual:
        raise AuditError('resume_orphan_trade_rows')
    return cursor, pages, count, exhausted


def failure_reason(exc):
    if isinstance(exc, AuditError):
        return str(exc)
    if isinstance(exc, HTTPError):
        return 'http_' + str(exc.code)
    reason = exc.reason if isinstance(exc, URLError) else exc
    if isinstance(reason, ssl.SSLCertVerificationError):
        return 'tls_verification_failed'
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return 'network_timeout'
    if isinstance(exc, sqlite3.Error):
        return 'sqlite_' + type(exc).__name__
    if isinstance(exc, (URLError, ConnectionError)):
        return 'network_error'
    if isinstance(exc, OSError):
        return 'storage_or_os_error'
    return 'invalid_response_' + type(exc).__name__


def transient(exc):
    if isinstance(exc, HTTPError):
        return exc.code in (500, 502, 503, 504)
    reason = exc.reason if isinstance(exc, URLError) else exc
    return isinstance(reason, (socket.timeout, TimeoutError, ConnectionError))


def audit(db, market, end_ms=None, now_ms=None, max_pages=400, seconds=180,
          fetch=request, clock=time.monotonic, pause=time.sleep, resume=None):
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    old_report = None
    if resume is not None:
        old = db.execute('SELECT market,start_ms,end_ms,report_json FROM cvd_backfill_runs '
                         'WHERE run_id=?', (resume,)).fetchone()
        if old is None or old[0] != market or (end_ms is not None and end_ms != old[2]):
            raise AuditError('resume_market_or_interval_mismatch')
        old_report = json.loads(old[3])
        if old_report.get('status') != 'incomplete' or old[1] != old[2] - WINDOW:
            raise AuditError('resume_requires_incomplete_run')
        end_ms = old[2]
    end_ms = now_ms // WINDOW * WINDOW if end_ms is None else end_ms
    if (market not in PATHS or type(now_ms) is not int or type(end_ms) is not int or
            end_ms % WINDOW or end_ms < WINDOW or end_ms > now_ms - 60000 or
            now_ms - end_ms > 89 * 86400000 or not 2 <= max_pages <= 2000 or
            not 1 <= seconds <= 600):
        raise AuditError('invalid_closed_interval_or_budget')
    start = end_ms - WINDOW
    run_id = resume or uuid.uuid4().hex
    report = dict(run_id=run_id, market=market, exchange='bitget', symbol='BTCUSDT',
                  start_ms=start, end_ms=end_ms, attempted_at_ms=now_ms, status='incomplete', reason='in_progress',
                  coverage_verified=False, value=None, candidate_delta_btc=None,
                  pages=0, recovered_trades=0, pagination_exhausted=False,
                  candle_match=False, journal_missing=None, journal_extra=None,
                  journal_conflicts=None, timestamp_rounding_matches=0,
                  request_attempts=0, transient_retries=0,
                  resume_count=(old_report.get('resume_count', 0) + 1) if old_report else 0)

    cursor = None
    if resume is not None:
        cursor, pages, count, exhausted = resume_checkpoint(db, run_id, start, end_ms)
        report.update(pages=pages, recovered_trades=count, pagination_exhausted=exhausted)

    def save():
        with db:
            db.execute('INSERT OR REPLACE INTO cvd_backfill_runs VALUES(?,?,?,?,?)',
                       (run_id, market, start, end_ms, json.dumps(report, sort_keys=True)))

    save()
    deadline = clock() + seconds
    params = dict(symbol='BTCUSDT', startTime=str(start), endTime=str(end_ms - 1), limit='1000')
    extra = {'productType': 'USDT-FUTURES'} if market == 'usdt_futures' else {}
    params.update(extra)

    def get(suffix, query):
        # Pace both trade and candle requests below the documented 10 requests/s.
        for attempt in range(3):
            pause(0.2 if attempt == 0 else attempt)
            remaining = deadline - clock()
            if remaining <= 0:
                raise AuditError('time_budget_exhausted')
            report['request_attempts'] += 1
            try:
                result = fetch(PATHS[market] + suffix, dict(query), min(10, remaining))
            except (URLError, OSError) as exc:
                # Never retry 429, access blocks, TLS errors or malformed data.
                retry = transient(exc)
                if isinstance(exc, HTTPError) and exc.fp is not None:
                    exc.close()
                if not retry or attempt == 2:
                    raise
                report['transient_retries'] += 1
                continue
            if clock() > deadline:
                raise AuditError('time_budget_exhausted')
            if not isinstance(result, dict) or result.get('code') != '00000' or not isinstance(result.get('data'), list):
                raise AuditError('invalid_api_response')
            return result

    try:
        first_page = report['pages'] + 1
        for page_no in range(first_page, first_page + max_pages):
            if report['pagination_exhausted']:
                break
            if cursor is not None:
                params['idLessThan'] = cursor
            response = get('fills-history', params)
            rows = response['data']
            parsed = parse_rows(rows, run_id, page_no, cursor, start, end_ms)
            next_cursor = rows[-1]['tradeId'] if rows else None
            payload = json.dumps(response, sort_keys=True, separators=(',', ':'))
            with db:
                db.executemany('INSERT INTO cvd_backfill_trades VALUES(?,?,?,?,?,?,?)', parsed)
                db.execute('INSERT INTO cvd_backfill_pages VALUES(?,?,?,?,?,?,?)',
                           (run_id, page_no, cursor, next_cursor, len(rows),
                            hashlib.sha256(payload.encode()).hexdigest(), payload))
            report['pages'] = page_no
            report['recovered_trades'] += len(rows)
            save()
            if not rows:
                report['pagination_exhausted'] = True
                break
            cursor = next_cursor
        if not report['pagination_exhausted']:
            raise AuditError('page_budget_exhausted')
        if not report['recovered_trades']:
            raise AuditError('empty_interval')

        query = dict(symbol='BTCUSDT', granularity='4h' if market == 'spot' else '4H',
                     endTime=str(end_ms), limit='2', **extra)
        candle_response = get('history-candles', query)
        candles = [r for r in candle_response['data']
                   if isinstance(r, list) and len(r) >= 7 and integer(r[0]) == start]
        if len(candles) != 1:
            raise AuditError('closed_candle_missing_or_duplicated')
        candle = candles[0]
        # Keep exact provider evidence local; no raw trades or candles in GitHub.
        report['candle_response_at_ms'] = candle_response.get('requestTime')
        report['candle_response_sha256'] = hashlib.sha256(
            json.dumps(candle_response, sort_keys=True).encode()).hexdigest()
        report['candle_row'] = candle
        with localcontext() as context:
            context.prec = 100
            base = quote = buy = sell = Decimal(0)
            for price, size, side in db.execute(
                    'SELECT price,size_btc,side FROM cvd_backfill_trades WHERE run_id=?', (run_id,)):
                amount = decimal(size)
                base += amount
                quote += decimal(price) * amount
                if side == 'buy':
                    buy += amount
                else:
                    sell += amount
            candle_base, candle_quote = decimal(candle[5], True), decimal(candle[6], True)
            report.update(base_btc=str(base), quote_usdt=str(quote),
                          candle_base_btc=str(candle_base), candle_quote_usdt=str(candle_quote),
                          candidate_buy_btc=str(buy), candidate_sell_btc=str(sell))
            report['candle_match'] = base == candle_base and quote == candle_quote
            delta = str(buy - sell)
            # A freshly closed candle can be served from a different cache than
            # fills-history. Use another documented endTime, selecting the SAME
            # closed candle by open timestamp; never accept another interval or
            # loosen volume equality. Preserve both responses for inspection.
            report['volume_reconciliation'] = volume_reconciliation(base, quote, candle_base, candle_quote)
            if not report['candle_match']:
                report['initial_candle_row'] = candle
                report['initial_volume_reconciliation'] = report['volume_reconciliation']
                refreshed = get('history-candles', dict(query, endTime=str(end_ms + 1)))
                matches = [r for r in refreshed['data'] if isinstance(r, list) and
                           len(r) >= 7 and integer(r[0]) == start]
                if len(matches) != 1:
                    raise AuditError('closed_candle_missing_or_duplicated')
                candle = matches[0]
                candle_base, candle_quote = decimal(candle[5], True), decimal(candle[6], True)
                report.update(candle_row=candle,
                              candle_base_btc=str(candle_base), candle_quote_usdt=str(candle_quote),
                              candle_rechecked=True,
                              candle_response_at_ms=refreshed.get('requestTime'),
                              candle_response_sha256=hashlib.sha256(
                                  json.dumps(refreshed, sort_keys=True).encode()).hexdigest())
                report['candle_match'] = base == candle_base and quote == candle_quote
            report['volume_reconciliation'] = volume_reconciliation(base, quote, candle_base, candle_quote)

        # One consistent read transaction for both directions of the journal comparison.
        with db:
            db.execute('BEGIN')
            report['journal_missing'] = db.execute('''SELECT COUNT(*) FROM cvd_backfill_trades c
              LEFT JOIN journal.trades j ON j.market=? AND j.trade_id=c.trade_id
              WHERE c.run_id=? AND j.trade_id IS NULL''', (market, run_id)).fetchone()[0]
            report['journal_extra'] = db.execute('''SELECT COUNT(*) FROM journal.trades j
              LEFT JOIN cvd_backfill_trades c ON c.run_id=? AND c.trade_id=j.trade_id
              WHERE j.market=? AND j.ts_ms>=? AND j.ts_ms<? AND c.trade_id IS NULL''',
                                                (run_id, market, start, end_ms)).fetchone()[0]
            conflicts = rounded = 0
            for cts, cp, cs, side, jts, jp, js, jside in db.execute('''
              SELECT c.ts_ms,c.price,c.size_btc,c.side,j.ts_ms,j.price,j.size_btc,j.taker_side
              FROM cvd_backfill_trades c JOIN journal.trades j
              ON j.market=? AND j.trade_id=c.trade_id WHERE c.run_id=?''', (market, run_id)):
                time_matches = type(jts) is int and cts == jts
                if (not time_matches and market == 'spot' and type(jts) is int and
                        cts % 1000 == 0 and cts // 1000 == jts // 1000):
                    time_matches = True
                    rounded += 1
                if not (time_matches and decimal(cp) == decimal(jp) and
                        decimal(cs) == decimal(js) and side == jside):
                    conflicts += 1
            report.update(journal_conflicts=conflicts, timestamp_rounding_matches=rounded)
        if not report['candle_match']:
            raise AuditError('candle_volume_mismatch')
        if report['journal_conflicts'] or report['journal_extra']:
            raise AuditError('journal_reconciliation_failed')
        report.update(status='provider_consistent', reason='candidate_requires_coverage_validation',
                      candidate_delta_btc=delta)
    except (AuditError, OSError, URLError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        db.rollback()
        report.update(status='incomplete', reason=failure_reason(exc))
    save()
    return report


def volume_reconciliation(base, quote, candle_base, candle_quote):
    """Describe a discrepancy, never turn a small discrepancy into verification."""
    with localcontext() as context:
        context.prec = 100
        def component(actual, reference):
            difference = actual - reference
            return dict(trades=str(actual), candle=str(reference), difference=str(difference),
                        difference_pct=str(difference / reference * 100) if reference else None,
                        exact=actual == reference)
        return dict(rule='exact_decimal_equality',
                    base_btc=component(base, candle_base),
                    quote_usdt=component(quote, candle_quote))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--journal', required=True)
    p.add_argument('--store', required=True)
    p.add_argument('--market', choices=tuple(PATHS), required=True)
    p.add_argument('--end-ms', type=int)
    p.add_argument('--max-pages', type=int, default=400)
    p.add_argument('--seconds', type=int, default=180)
    p.add_argument('--resume', help='Continue an incomplete run in the candidate store')
    args = p.parse_args()
    os.umask(0o077)
    import fcntl
    lock_path = Path(args.store).resolve().with_suffix('.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        db = open_store(args.store, args.journal)
        try:
            report = audit(db, args.market, args.end_ms,
                           max_pages=args.max_pages, seconds=args.seconds, resume=args.resume)
        finally:
            db.close()
    # Aggregate summary only; full candle evidence remains in the private store.
    print(json.dumps({k: v for k, v in report.items() if k != 'candle_row'}, indent=2))
    return 0 if report['status'] == 'provider_consistent' else 1


if __name__ == '__main__':
    sys.exit(main())
