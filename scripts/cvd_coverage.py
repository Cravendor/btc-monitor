"""Replay local Bitget history evidence; attest provider coverage, not all venues.

Buy/sell is the provider's reported convention. This is not an independent
verification of taker attribution and not a cumulative CVD baseline.
"""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import sqlite3

if __package__:
    from .cvd_backfill import AuditError, WINDOW, decimal, integer, resume_checkpoint
else:
    from cvd_backfill import AuditError, WINDOW, decimal, integer, resume_checkpoint

METHOD = 'bitget_history_exhaustion_and_exact_volume_v1'
MARKETS = ('spot', 'usdt_futures')


def verify(db, run_id, market, end_ms, now_ms):
    """Caller supplies a consistent read transaction with journal attached read-only."""
    if (market not in MARKETS or type(end_ms) is not int or end_ms % WINDOW or
            end_ms < WINDOW or end_ms > now_ms - 60000):
        raise AuditError('invalid_closed_interval')
    start = end_ms - WINDOW
    row = db.execute('SELECT market,start_ms,end_ms,report_json FROM cvd_backfill_runs '
                     'WHERE run_id=?', (run_id,)).fetchone()
    if row is None or row[:3] != (market, start, end_ms):
        raise AuditError('coverage_run_identity_mismatch')
    report = json.loads(row[3])
    if (not isinstance(report, dict) or report.get('status') != 'provider_consistent' or report.get('run_id') != run_id or
            report.get('market') != market or report.get('exchange') != 'bitget' or
            report.get('symbol') != 'BTCUSDT' or report.get('start_ms') != start or
            report.get('end_ms') != end_ms):
        raise AuditError('candidate_not_consistent')
    _, pages, count, exhausted = resume_checkpoint(db, run_id, start, end_ms)
    if not exhausted or not count or report.get('pages') != pages or report.get('recovered_trades') != count:
        raise AuditError('coverage_history_not_exhausted')
    candle = report.get('candle_row')
    if not isinstance(candle, list) or len(candle) < 7 or integer(candle[0]) != start:
        raise AuditError('coverage_candle_identity_mismatch')
    with localcontext() as context:
        context.prec = 100
        buy = sell = base = quote = Decimal(0)
        first = last = None
        for ts, price, size, side in db.execute(
                'SELECT ts_ms,price,size_btc,side FROM cvd_backfill_trades WHERE run_id=?', (run_id,)):
            amount = decimal(size)
            base += amount
            quote += decimal(price) * amount
            if side == 'buy':
                buy += amount
            elif side == 'sell':
                sell += amount
            else:
                raise AuditError('coverage_invalid_side')
            first = ts if first is None else min(first, ts)
            last = ts if last is None else max(last, ts)
        if base != decimal(candle[5], True) or quote != decimal(candle[6], True):
            raise AuditError('coverage_volume_mismatch')
        delta = format(buy - sell, 'f')
        if (decimal(report.get('candidate_buy_btc'), True) != buy or
                decimal(report.get('candidate_sell_btc'), True) != sell or
                Decimal(report.get('candidate_delta_btc')) != buy - sell):
            raise AuditError('coverage_aggregate_mismatch')

    missing = db.execute('''SELECT COUNT(*) FROM cvd_backfill_trades c
      LEFT JOIN journal.trades j ON j.market=? AND j.trade_id=c.trade_id
      WHERE c.run_id=? AND j.trade_id IS NULL''', (market, run_id)).fetchone()[0]
    extra = db.execute('''SELECT COUNT(*) FROM journal.trades j
      LEFT JOIN cvd_backfill_trades c ON c.run_id=? AND c.trade_id=j.trade_id
      WHERE j.market=? AND j.ts_ms>=? AND j.ts_ms<? AND c.trade_id IS NULL''',
                       (run_id, market, start, end_ms)).fetchone()[0]
    if extra:
        raise AuditError('coverage_journal_extra_trades')
    rounded = 0
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
            raise AuditError('coverage_journal_conflict')

    digest = hashlib.sha256()
    for (sha,) in db.execute('SELECT response_sha256 FROM cvd_backfill_pages '
                            'WHERE run_id=? ORDER BY page_no', (run_id,)):
        digest.update(sha.encode())
    digest.update(json.dumps(candle, separators=(',', ':')).encode())
    last_payload = db.execute('SELECT payload_json FROM cvd_backfill_pages WHERE run_id=? '
                              'ORDER BY page_no DESC LIMIT 1', (run_id,)).fetchone()[0]
    provider_time = json.loads(last_payload).get('requestTime')
    try:
        response_at = datetime.fromtimestamp(integer(provider_time)/1000, timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        response_at = None
    return dict(status='ok', value=delta, validated_delta_btc=delta,
                coverage_verified=True, coverage_scope='bitget_public_history_only',
                coverage_method=METHOD, unit='BTC', exchange='bitget', symbol='BTCUSDT',
                market=market, interval_start_ms=start, interval_end_ms=end_ms,
                trade_count=count, validated_buy_btc=format(buy, 'f'),
                validated_sell_btc=format(sell, 'f'), first_trade_ms=first, last_trade_ms=last,
                recovered_missing_trades=missing, timestamp_rounding_matches=rounded,
                pagination_pages=pages, evidence_sha256=digest.hexdigest(),
                source_run_id=run_id, history_response_at=response_at,
                validated_at=datetime.fromtimestamp(
                    now_ms / 1000, timezone.utc).isoformat(),
                side_semantics='provider_reported_buy_sell', taker_side_verified=False,
                reason='Provider history exhausted and exact BTC/quote volumes reconciled; '
                       'not independent proof of all exchange delivery or taker attribution.')


def read_verified(store, journal, end_ms, now_ms):
    """Always replay evidence; never trust a saved green status or an old interval."""
    if not store or not journal:
        return {}
    db = None
    try:
        path, journal = Path(store).resolve(), Path(journal).resolve()
        if not path.is_file() or not journal.is_file() or path == journal:
            return {}
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
        db.execute('PRAGMA query_only=ON')
        db.execute('ATTACH DATABASE ? AS journal', (journal.as_uri() + '?mode=ro',))
        db.execute('BEGIN')
        result = {}
        for market in MARKETS:
            # An incomplete newer retry must not hide an intact completed run.
            for (run_id,) in db.execute('SELECT run_id FROM cvd_backfill_runs '
                                       'WHERE market=? AND start_ms=? AND end_ms=? '
                                       'ORDER BY rowid DESC', (market, end_ms - WINDOW, end_ms)):
                try:
                    result[market] = verify(db, run_id, market, end_ms, now_ms)
                    break
                except (AuditError, ValueError, TypeError, KeyError, ArithmeticError):
                    continue
        return result
    except (OSError, sqlite3.Error, ValueError, TypeError, OverflowError):
        return {}
    finally:
        if db is not None:
            db.close()
