"""Fail-closed validation for a future complete, venue-specific CVD trade collector.

No API is called here. A five-trade sample must NEVER be reported as 4H CVD.
"""
from datetime import datetime, timezone

INTERVAL_MS = 4 * 60 * 60 * 1000


def validate_coverage(trades, start_ms, end_ms, *, source_complete=False,
                      gaps_checked=False, pagination_complete=False):
    """Validate UTC interval and explicit collector attestations.

    Each trade: {'id': unique venue trade ID, 'ts_ms': epoch milliseconds,
                 'size_btc': nonnegative numeric, 'side': 'buy'|'sell'}.
    'side' MUST mean taker/aggressor side, not maker side.
    """
    result = {'status': 'incomplete', 'value': None, 'start_ms': start_ms,
              'end_ms': end_ms, 'trade_count': 0, 'reason': None}
    if not isinstance(start_ms, int) or not isinstance(end_ms, int) or end_ms-start_ms != INTERVAL_MS or start_ms % INTERVAL_MS:
        result['reason'] = 'Invalid aligned UTC 4H window'
        return result
    if end_ms > int(datetime.now(timezone.utc).timestamp()*1000):
        result['reason'] = 'Window has not closed'
        return result
    if not (source_complete and gaps_checked and pagination_complete):
        result['reason'] = 'Complete source interval, gap checks and pagination are not all attested'
        return result
    if not isinstance(trades, list) or not trades:
        result['reason'] = 'No validated trades'
        return result
    ids = set()
    delta = 0.0
    for trade in trades:
        try:
            tid = str(trade['id'])
            ts = trade['ts_ms']
            size = float(trade['size_btc'])
            side = trade['side']
            if not tid or tid in ids or not isinstance(ts, int) or not start_ms <= ts < end_ms:
                raise ValueError('Duplicate ID or out-of-window trade')
            if size < 0 or size != size or size == float('inf') or side not in ('buy', 'sell'):
                raise ValueError('Invalid trade size or aggressor side')
        except (KeyError, TypeError, ValueError, OverflowError):
            result['reason'] = 'Invalid, duplicate or out-of-window trade'
            return result
        ids.add(tid)
        delta += size if side == 'buy' else -size
    result.update(status='ok', value=delta, trade_count=len(ids),
                  reason=None, unit='BTC', scope='venue-specific taker buy minus taker sell')
    return result
