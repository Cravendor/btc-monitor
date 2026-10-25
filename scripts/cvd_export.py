"""Read journal observations and optionally verified Bitget public-history deltas."""
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

WINDOW_MS = 4 * 60 * 60 * 1000
MARKETS = ('spot', 'usdt_futures')
REASON = 'No verified Bitget public-history coverage for this interval.'


def timestamp(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


def unavailable(reason, status='missing_data'):
    return {'status': status, 'value': None, 'coverage_verified': False,
            'reason': reason}


def read_market(db, market, start, end, now_ms):
    result = unavailable(REASON, 'partial')
    result.update(unit='BTC', observed_delta_btc=None, observed_buy_btc=None,
                  observed_sell_btc=None, trade_count=0,
                  first_trade_at=None, last_trade_at=None)
    gaps, open_gaps = db.execute('''
        SELECT COUNT(*), COALESCE(SUM(end_ms IS NULL), 0) FROM gaps
        WHERE market=? AND resolved=0 AND start_ms < ?
          AND (end_ms IS NULL OR end_ms > ?)
    ''', (market, end, start)).fetchone()
    result.update(unresolved_overlapping_gaps=gaps, open_overlapping_gaps=open_gaps)
    latest = db.execute('''
        SELECT ts_ms FROM trades WHERE market=? ORDER BY ts_ms DESC LIMIT 1
    ''', (market,)).fetchone()
    if latest is not None:
        if type(latest[0]) is not int or not 0 < latest[0] <= now_ms + 60000:
            return unavailable('Invalid or future journal trade timestamp.', 'invalid_data')
        age = max(0, (now_ms - latest[0]) / 1000)
        result.update(latest_journal_trade_at=timestamp(latest[0]),
                      latest_journal_trade_age_seconds=round(age, 3),
                      journal_trade_status='stale' if age > 300 else 'recent')
    else:
        result.update(latest_journal_trade_at=None,
                      latest_journal_trade_age_seconds=None,
                      journal_trade_status='missing_data')
    # Decimal strings retain BTC precision. SQLite SUM would convert to floats.
    with localcontext() as ctx:
        ctx.prec = 80
        buy = sell = Decimal(0)
        first = last = None
        count = 0
        for ts, size, side in db.execute('''
            SELECT ts_ms,size_btc,taker_side FROM trades
            WHERE market=? AND ts_ms >= ? AND ts_ms < ? ORDER BY ts_ms
        ''', (market, start, end)):
            try:
                value = Decimal(str(size))
                if (type(ts) is not int or not start <= ts < end or
                        side not in ('buy', 'sell') or not value.is_finite() or
                        value <= 0 or len(value.as_tuple().digits) > 30 or
                        not -30 <= value.as_tuple().exponent <= 10):
                    raise ValueError('Invalid stored trade')
            except (InvalidOperation, ValueError, TypeError):
                return unavailable('Invalid stored trade; interval delta withheld.', 'invalid_data')
            if side == 'buy':
                buy += value
            else:
                sell += value
            first = ts if first is None else first
            last = ts
            count += 1
        if count:
            result.update(observed_delta_btc=format(buy - sell, 'f'),
                          observed_buy_btc=format(buy, 'f'),
                          observed_sell_btc=format(sell, 'f'), trade_count=count,
                          first_trade_at=timestamp(first), last_trade_at=timestamp(last))
        else:
            result.update(status='missing_data', reason='No observed trades in this closed interval.')
    return result


def collect_cvd(path=None, now=None, backfill_path=None):
    """One consistent read transaction; no schema migration, writes or raw trade export."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Timezone-aware time required')
    now_ms = int(now.timestamp() * 1000)
    end = now_ms // WINDOW_MS * WINDOW_MS
    start = end - WINDOW_MS
    result = unavailable(REASON, 'partial')
    result.update(schema_version=1, exchange='bitget', symbol='BTCUSDT',
                  unit='BTC', method='observed_buy_minus_sell',
                  interval_start=timestamp(start), interval_end=timestamp(end),
                  interval_convention='[start,end)', observed_at=now.isoformat(),
                  markets={})
    path = path if path is not None else os.environ.get('BTC_CVD_DB')
    if not path:
        result.update(status='not_collected', reason='Local CVD journal is not configured.')
        return result
    db = None
    try:
        source = Path(path).resolve()
        if not source.is_file():
            raise OSError('Missing journal')
        db = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=5)
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        result['markets'] = {market: read_market(db, market, start, end, now_ms)
                             for market in MARKETS}
        if any(m['status'] == 'invalid_data' for m in result['markets'].values()):
            result.update(status='invalid_data', reason='One or more journal markets contain invalid trades.')
        elif all(m['status'] == 'missing_data' for m in result['markets'].values()):
            result.update(status='missing_data', reason='No observed trades in this closed interval.')
    except (OSError, sqlite3.Error, OverflowError, ValueError):
        # Do not leak private paths, SQL or exception details into the public feed.
        result.update(status='missing_data', reason='Local CVD journal unavailable or incompatible.',
                      markets={market: unavailable('Journal unavailable or incompatible.') for market in MARKETS})
    finally:
        if db is not None:
            db.close()
    # Cloud/manual runs never silently reuse NAS evidence from inherited env vars.
    if backfill_path is None and os.environ.get('BTC_COLLECTOR_SOURCE') == 'nas':
        backfill_path = os.environ.get('BTC_CVD_BACKFILL_STORE')
    if backfill_path:
        if __package__:
            from .cvd_coverage import read_verified, read_diagnostics
        else:
            from cvd_coverage import read_verified, read_diagnostics
        diagnostics = read_diagnostics(backfill_path, end)
        for market, diagnostic in diagnostics.items():
            result['markets'].setdefault(market, unavailable(REASON, 'partial'))['recovery'] = diagnostic
        verified = read_verified(backfill_path, path, end, now_ms)
        for market, proof in verified.items():
            observed = result['markets'].get(market, {})
            observed['observed_trade_count'] = observed.get('trade_count')
            observed.update(proof)
            observed['first_trade_at'] = timestamp(proof['first_trade_ms'])
            observed['last_trade_at'] = timestamp(proof['last_trade_ms'])
            result['markets'][market] = observed
        if verified:
            result.update(schema_version=2, method='provider_reported_buy_minus_sell',
                          coverage_scope='bitget_public_history_only',
                          side_semantics='provider_reported_buy_sell', taker_side_verified=False)
            if len(verified) == 2:
                result.update(status='ok', coverage_verified=True,
                              reason='Both Bitget markets passed stored history coverage checks; '
                                     'deltas use the provider buy/sell convention.')
            else:
                result.update(status='partial', coverage_verified=False,
                              reason='Only one Bitget market has verified history coverage.')
    return result
