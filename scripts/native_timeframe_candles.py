"""Validate native Bitget closed candles for multi-timeframe signals.

Read-only helpers; no API calls or credentials. Bitget 1W boundaries use
exchange-specific alignment and must be checked against a documented calendar
before 1W is enabled.
"""
from datetime import datetime, timezone
from math import isfinite

GRANULARITIES = {"5m": "5m", "15m": "15m", "30m": "30m",
                 "1h": "1H", "4h": "4H", "1d": "1D"}
PERIOD_MS = {"5m": 300000, "15m": 900000, "30m": 1800000,
             "1h": 3600000, "4h": 14400000, "1d": 86400000}


def validate_rows(rows, timeframe, as_of):
    if timeframe not in GRANULARITIES:
        raise ValueError("unsupported native timeframe")
    now = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if now.tzinfo is None:
        raise ValueError("timezone required")
    period = PERIOD_MS[timeframe]
    boundary = int(now.timestamp() * 1000) // period * period
    if not isinstance(rows, list):
        raise ValueError("expected candle list")
    parsed = {}
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 7:
            raise ValueError("invalid candle row")
        try:
            ts = int(row[0])
            o, h, l, c, volume, quote = map(float, row[1:7])
        except (ValueError, TypeError):
            raise ValueError("invalid candle field") from None
        if (ts % period or not all(isfinite(v) for v in (o, h, l, c, volume, quote))
                or min(o, h, l, c) <= 0 or min(volume, quote) < 0
                or l > min(o, c) or h < max(o, c)):
            raise ValueError("invalid candle geometry")
        if ts >= boundary:
            continue
        entry = {"open_time_ms": ts, "open": o, "high": h,
                 "low": l, "close": c, "base_volume_btc": volume,
                 "quote_volume_usdt": quote}
        if ts in parsed and parsed[ts] != entry:
            raise ValueError("conflicting duplicate candle")
        parsed[ts] = entry
    ordered = [parsed[t] for t in sorted(parsed)]
    if len(ordered) < 24 or ordered[-1]["open_time_ms"] != boundary - period:
        raise ValueError("missing latest closed candle or insufficient coverage")
    if any(b["open_time_ms"] - a["open_time_ms"] != period
           for a, b in zip(ordered[-24:], ordered[-23:])):
        raise ValueError("non-contiguous recent candles")
    return {"candles": ordered, "interval": timeframe, "closed_only": True,
            "gap_count": sum(b["open_time_ms"] - a["open_time_ms"] != period
                             for a, b in zip(ordered, ordered[1:]))}
