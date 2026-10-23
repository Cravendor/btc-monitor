"""UTC multi-timeframe aggregation of venue trade journals.

Outputs observed deltas, never claims verified complete CVD. A WebSocket
snapshot is not a full interval and connection uptime cannot prove coverage.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal

WINDOWS = {"1m": 60_000, "5m": 300_000, "15m": 900_000,
           "30m": 1_800_000, "1h": 3_600_000, "4h": 14_400_000,
           "1d": 86_400_000, "1w": 604_800_000}
WEEK_ANCHOR_MS = 4 * 86_400_000  # Monday 1970-01-05 UTC

def aligned_start(ts_ms, timeframe):
    width = WINDOWS[timeframe]
    anchor = WEEK_ANCHOR_MS if timeframe == "1w" else 0
    return ((ts_ms - anchor) // width) * width + anchor

def observed_window(db, market, timeframe, start_ms, *, now_ms=None):
    if market not in ("spot", "usdt_futures") or timeframe not in WINDOWS:
        raise ValueError("Unsupported market or timeframe")
    if aligned_start(start_ms, timeframe) != start_ms:
        raise ValueError("Window not UTC aligned")
    if now_ms is None:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    end_ms = start_ms + WINDOWS[timeframe]
    rows = db.execute(
        "SELECT size_btc,taker_side FROM trades WHERE market=? AND ts_ms>=? AND ts_ms<?",
        (market, start_ms, end_ms)).fetchall()
    buys = sum((Decimal(size) for size, side in rows if side == "buy"), Decimal(0))
    sells = sum((Decimal(size) for size, side in rows if side == "sell"), Decimal(0))
    gap_count = db.execute(
        """SELECT COUNT(*) FROM gaps WHERE market=? AND resolved=0
           AND start_ms<? AND COALESCE(end_ms, ?) > ?""",
        (market, end_ms, now_ms, start_ms)).fetchone()[0]
    return {"market": market, "timeframe": timeframe,
            "start_ms": start_ms, "end_ms": end_ms,
            "status": "incomplete" if end_ms <= now_ms else "open",
            "coverage_verified": False,
            "unresolved_gaps": gap_count,
            "trade_count": len(rows),
            "observed_taker_buy_btc": str(buys),
            "observed_taker_sell_btc": str(sells),
            "observed_delta_btc": str(buys - sells),
            "cvd": None,
            "reason": "No independently verified full trade coverage"}

def latest_closed_windows(db, *, now_ms=None):
    if now_ms is None:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {"generated_ms": now_ms, "status": "unverified_observations",
            "windows": [
                observed_window(db, market, tf, aligned_start(now_ms - 1, tf) -
                                WINDOWS[tf], now_ms=now_ms)
                for market in ("spot", "usdt_futures") for tf in WINDOWS
            ]}
