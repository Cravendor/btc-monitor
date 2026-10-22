"""Persistent trade journal for a future Bitget CVD stream.

This module does NOT attest to complete interval coverage. Never publish its
raw sum as validated CVD without independent gap/backfill verification.
"""
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
 market TEXT NOT NULL,
 trade_id TEXT NOT NULL,
 ts_ms INTEGER NOT NULL,
 received_ms INTEGER NOT NULL,
 price TEXT NOT NULL,
 size_btc TEXT NOT NULL,
 taker_side TEXT NOT NULL CHECK(taker_side IN ('buy','sell')),
 PRIMARY KEY (market, trade_id)
);
CREATE INDEX IF NOT EXISTS trades_by_window ON trades(market, ts_ms);
CREATE TABLE IF NOT EXISTS gaps (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 market TEXT NOT NULL,
 start_ms INTEGER NOT NULL,
 end_ms INTEGER,
 reason TEXT NOT NULL,
 resolved INTEGER NOT NULL DEFAULT 0
);
"""

def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db

def record_trade(db, *, market, trade_id, ts_ms, received_ms, price, size_btc, taker_side):
    if market not in ("spot", "usdt_futures") or taker_side not in ("buy", "sell"):
        raise ValueError("Unsupported market or taker side")
    if not trade_id or not isinstance(ts_ms, int) or not isinstance(received_ms, int):
        raise ValueError("Invalid trade identifier or timestamp")
    from decimal import Decimal
    if not (Decimal(str(price)).is_finite() and Decimal(str(price)) > 0 and
            Decimal(str(size_btc)).is_finite() and Decimal(str(size_btc)) > 0):
        raise ValueError("Invalid price or size")
    cursor = db.execute(
        "INSERT OR IGNORE INTO trades VALUES (?, ?, ?, ?, ?, ?, ?)",
        (market, str(trade_id), ts_ms, received_ms, str(price), str(size_btc), taker_side))
    db.commit()
    return cursor.rowcount == 1

def record_gap(db, *, market, start_ms, end_ms=None, reason):
    if market not in ("spot", "usdt_futures") or not reason:
        raise ValueError("Invalid gap")
    db.execute("INSERT INTO gaps(market,start_ms,end_ms,reason) VALUES (?,?,?,?)",
               (market, start_ms, end_ms, reason))
    db.commit()

def export_health(db, output):
    """Export only journal health; no invented CVD completeness."""
    result = {"status": "collection_preparation_only", "cvd_4h": None,
              "markets": {}}
    for market in ("spot", "usdt_futures"):
        count, first, last = db.execute(
            "SELECT COUNT(*),MIN(ts_ms),MAX(ts_ms) FROM trades WHERE market=?", (market,)
        ).fetchone()
        unresolved = db.execute(
            "SELECT COUNT(*) FROM gaps WHERE market=? AND resolved=0", (market,)
        ).fetchone()[0]
        result["markets"][market] = {"trade_count": count, "first_trade_ms": first,
                                     "last_trade_ms": last, "unresolved_gaps": unresolved,
                                     "coverage_verified": False}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return result
