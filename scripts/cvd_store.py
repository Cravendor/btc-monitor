"""Additive journal/session evidence. Transport continuity is NOT trade coverage.

Compatible with the original NAS trades/gaps tables and Python 3.8+. Legacy
gap rows are never changed. Use one collector process under the existing flock.
"""
import json
import sqlite3
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

MARKETS = ("spot", "usdt_futures")
SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
 market TEXT NOT NULL, trade_id TEXT NOT NULL, ts_ms INTEGER NOT NULL,
 received_ms INTEGER NOT NULL, price TEXT NOT NULL, size_btc TEXT NOT NULL,
 taker_side TEXT NOT NULL CHECK(taker_side IN ('buy','sell')),
 PRIMARY KEY (market, trade_id)
);
CREATE INDEX IF NOT EXISTS trades_by_window ON trades(market, ts_ms);
CREATE TABLE IF NOT EXISTS gaps (
 id INTEGER PRIMARY KEY AUTOINCREMENT, market TEXT NOT NULL,
 start_ms INTEGER NOT NULL, end_ms INTEGER, reason TEXT NOT NULL,
 resolved INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS cvd_sessions (
 session_id TEXT PRIMARY KEY, market TEXT NOT NULL, instrument TEXT NOT NULL,
 started_ms INTEGER NOT NULL, subscribed_ms INTEGER, last_frame_ms INTEGER,
 last_trade_ms INTEGER, ended_ms INTEGER, state TEXT NOT NULL,
 end_reason TEXT, frame_count INTEGER NOT NULL DEFAULT 0,
 inserted_trades INTEGER NOT NULL DEFAULT 0,
 duplicate_trades INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS cvd_sessions_market ON cvd_sessions(market, started_ms);
CREATE TABLE IF NOT EXISTS cvd_owned_gaps (
 gap_id INTEGER PRIMARY KEY, market TEXT NOT NULL
);
"""


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db


def _timestamp(value):
    if type(value) is not int or value < 0:
        raise ValueError("Invalid millisecond timestamp")
    return value


def _session(db, session_id):
    row = db.execute("SELECT market,started_ms,last_frame_ms,state FROM cvd_sessions "
                     "WHERE session_id=?", (session_id,)).fetchone()
    if row is None or row[3] not in ("connecting", "subscribed"):
        raise ValueError("Session is not active")
    return row


def _gap(db, market, start_ms, reason, end_ms=None):
    cursor = db.execute("INSERT INTO gaps(market,start_ms,end_ms,reason) VALUES(?,?,?,?)",
                        (market, start_ms, end_ms, reason))
    db.execute("INSERT INTO cvd_owned_gaps VALUES(?,?)", (cursor.lastrowid, market))


def begin_session(db, market, at_ms):
    """Recover abandoned attempts after a crash, without inventing their end time."""
    if market not in MARKETS:
        raise ValueError("Unsupported market")
    _timestamp(at_ms)
    session_id = uuid.uuid4().hex
    with db:
        previous = db.execute("SELECT started_ms,last_frame_ms FROM cvd_sessions "
                              "WHERE market=? AND ended_ms IS NULL", (market,)).fetchall()
        # The prior writer may have died at any point after its durable checkpoint.
        start = min([at_ms] + [frame if frame is not None else begun
                                  for begun, frame in previous])
        db.execute("UPDATE cvd_sessions SET state='interrupted', "
                   "ended_ms=COALESCE(last_frame_ms,started_ms), "
                   "end_reason='previous process ended without final checkpoint' "
                   "WHERE market=? AND ended_ms IS NULL", (market,))
        _gap(db, market, start, "session start/reconnect; delivery unverified")
        db.execute("INSERT INTO cvd_sessions(session_id,market,instrument,started_ms,state) "
                   "VALUES(?,?,'BTCUSDT',?,'connecting')", (session_id, market, at_ms))
    return session_id


def acknowledge(db, session_id, at_ms):
    _timestamp(at_ms)
    with db:
        market, begun, frame, state = _session(db, session_id)
        if state != "connecting" or at_ms < max(begun, frame or 0):
            raise ValueError("Invalid acknowledgement or clock regression")
        db.execute("UPDATE cvd_sessions SET subscribed_ms=?,last_frame_ms=?, "
                   "frame_count=frame_count+1,state='subscribed' WHERE session_id=?",
                   (at_ms, at_ms, session_id))
        # A bounded outage is still UNRESOLVED. Only our own markers are bounded;
        # yesterday's legacy OPEN rows retain their original meaning and values.
        db.execute("UPDATE gaps SET end_ms=MAX(start_ms,?) WHERE end_ms IS NULL "
                   "AND id IN (SELECT gap_id FROM cvd_owned_gaps WHERE market=?)",
                   (at_ms, market))


def record_frame(db, session_id, at_ms, trades=()):
    """Commit one validated frame and its checkpoint atomically; reject conflicts."""
    _timestamp(at_ms)
    with db:
        market, begun, last_frame, state = _session(db, session_id)
        if at_ms < max(begun, last_frame or 0) or state != "subscribed":
            raise ValueError("Frame before subscription or clock regression")
        inserted = duplicates = 0
        last_trade = None
        for trade in trades:
            trade_id, ts, price, size, side = trade
            _timestamp(ts)
            if not isinstance(trade_id, str) or not trade_id or side not in ("buy", "sell"):
                raise ValueError("Invalid trade identity or side")
            try:
                price_dec, size_dec = Decimal(str(price)), Decimal(str(size))
                if not (price_dec.is_finite() and price_dec > 0 and
                        size_dec.is_finite() and size_dec > 0):
                    raise ValueError("Invalid price or size")
            except (InvalidOperation, TypeError):
                raise ValueError("Invalid price or size")
            if ts > at_ms + 60000:
                raise ValueError("Trade timestamp too far in future")
            existing = db.execute("SELECT ts_ms,price,size_btc,taker_side FROM trades "
                                  "WHERE market=? AND trade_id=?", (market, trade_id)).fetchone()
            if existing:
                if (existing[0] != ts or Decimal(existing[1]) != price_dec or
                        Decimal(existing[2]) != size_dec or existing[3] != side):
                    raise ValueError("Conflicting replay for trade ID")
                duplicates += 1
            else:
                db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)",
                           (market, trade_id, ts, at_ms, str(price), str(size), side))
                inserted += 1
            last_trade = max(last_trade or 0, ts)
        db.execute("UPDATE cvd_sessions SET last_frame_ms=?,frame_count=frame_count+1, "
                   "last_trade_ms=CASE WHEN ? IS NULL THEN last_trade_ms "
                   "ELSE MAX(COALESCE(last_trade_ms,0),?) END, "
                   "inserted_trades=inserted_trades+?,duplicate_trades=duplicate_trades+? "
                   "WHERE session_id=?",
                   (at_ms, last_trade, last_trade, inserted, duplicates, session_id))
    return inserted


def end_session(db, session_id, at_ms, reason, stopped=False):
    _timestamp(at_ms)
    with db:
        market, begun, frame, _ = _session(db, session_id)
        start = min(at_ms, frame if frame is not None else begun)
        _gap(db, market, start, "session ended; delivery unverified: " + reason[:160])
        db.execute("UPDATE cvd_sessions SET ended_ms=?,state=?,end_reason=? "
                   "WHERE session_id=?", (at_ms, "stopped" if stopped else "disconnected",
                                          reason[:180], session_id))


def export_health(db, output):
    result = {"status": "collection_preparation_only", "cvd_4h": None, "markets": {}}
    with db:
        # Explicit read transaction: both markets reflect the same WAL snapshot.
        db.execute("BEGIN")
        for market in MARKETS:
            count, first, last = db.execute(
                "SELECT COUNT(*),MIN(ts_ms),MAX(ts_ms) FROM trades WHERE market=?", (market,)
            ).fetchone()
            unresolved = db.execute("SELECT COUNT(*) FROM gaps WHERE market=? AND resolved=0",
                                    (market,)).fetchone()[0]
            row = db.execute("SELECT session_id,state,started_ms,subscribed_ms,last_frame_ms,"
                             "last_trade_ms,ended_ms,end_reason,frame_count,inserted_trades,"
                             "duplicate_trades FROM cvd_sessions WHERE market=? "
                             "ORDER BY rowid DESC LIMIT 1", (market,)).fetchone()
            keys = ("session_id", "state", "started_ms", "subscribed_ms", "last_frame_ms",
                    "last_trade_ms", "ended_ms", "end_reason", "frame_count",
                    "inserted_trades", "duplicate_trades")
            result["markets"][market] = {
                "trade_count": count, "first_trade_ms": first, "last_trade_ms": last,
                "unresolved_gaps": unresolved, "coverage_verified": False,
                "transport_session": dict(zip(keys, row)) if row else None}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return result
