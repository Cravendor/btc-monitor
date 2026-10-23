"""Optional replacement NAS recorder, Python 3.8+, websocket-client required.

Run under the existing collector.lock. No backfill or complete CVD assertion.
Not installed or started by the periodic NAS snapshot task.
"""
import argparse
import json
import logging
import signal
import threading
import time
from decimal import InvalidOperation

try:
    from scripts import cvd_store as store
except ImportError:
    import cvd_store as store

URL = "wss://ws.bitget.com/v2/ws/public"
STREAMS = {"SPOT": "spot", "USDT-FUTURES": "usdt_futures"}
STOP = threading.Event()


def now_ms():
    return int(time.time() * 1000)


def consume_connection(ws, timeout_error, db, session_id, inst, stop=STOP):
    """Validate identity and ACK before journaling; caller closes every attempt."""
    arg = {"instType": inst, "channel": "trade", "instId": "BTCUSDT"}
    ws.settimeout(5)
    ws.send(json.dumps({"op": "subscribe", "args": [arg]}))
    started = last_inbound = last_ping = time.monotonic()
    subscribed = False
    while not stop.is_set():
        current = time.monotonic()
        if not subscribed and current - started > 15:
            raise TimeoutError("subscription acknowledgement timeout")
        if current - last_inbound > 35:
            raise TimeoutError("no inbound frames")
        # Same-thread sends avoid leaving a ping worker attached to an old socket.
        # Checking on every iteration also sends pings during a busy trade stream.
        if current - last_ping >= 25:
            ws.send("ping")
            last_ping = current
        try:
            raw = ws.recv()
        except timeout_error:
            continue
        last_inbound = time.monotonic()
        received = now_ms()
        if raw == "pong":
            if subscribed:
                store.record_frame(db, session_id, received)
            continue
        if not isinstance(raw, str) or not raw:
            raise ValueError("empty or binary frame")
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError("frame must be an object")
        if obj.get("event") == "error":
            # Persist a fixed reason, never arbitrary remote contents.
            raise ValueError("subscription error")
        if obj.get("arg") != arg:
            raise ValueError("unexpected market, symbol or channel")
        if obj.get("event") == "subscribe":
            if subscribed:
                raise ValueError("unexpected repeated acknowledgement")
            store.acknowledge(db, session_id, received)
            subscribed = True
            continue
        if not subscribed:
            raise ValueError("trade frame before acknowledgement")
        if obj.get("action") not in ("snapshot", "update"):
            raise ValueError("unsupported trade action")
        data = obj.get("data")
        if not isinstance(data, list):
            raise ValueError("trade data must be a list")
        trades = []
        for trade in data:
            if not isinstance(trade, dict):
                raise ValueError("trade must be an object")
            ts = trade["ts"]
            if not isinstance(ts, str) or not ts.isascii() or not ts.isdecimal():
                raise ValueError("invalid exchange timestamp")
            trades.append((trade["tradeId"], int(ts), trade["price"],
                           trade["size"], trade["side"]))
        store.record_frame(db, session_id, received, trades)


def run_attempt(client, db, inst, stop=STOP):
    session_id = store.begin_session(db, STREAMS[inst], now_ms())
    ws = None
    reason = "stop requested"
    try:
        ws = client.create_connection(URL, timeout=15, enable_multithread=True)
        consume_connection(ws, client.WebSocketTimeoutException, db, session_id, inst, stop)
    except Exception as exc:
        # Stable reason codes prevent remote frames or URLs leaking into health.
        if isinstance(exc, (ValueError, KeyError, TypeError, InvalidOperation, OverflowError)):
            reason = "invalid frame or trade"
        elif isinstance(exc, TimeoutError):
            reason = "connection or subscription timeout"
        else:
            reason = "connection or journal failure"
        logging.warning("%s: %s (%s)", STREAMS[inst], reason, type(exc).__name__)
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        store.end_session(db, session_id, now_ms(), reason, stopped=stop.is_set())


def consume(client, inst, path):
    db = store.connect(path)
    retry = 0
    try:
        while not STOP.is_set():
            run_attempt(client, db, inst)
            retry = min(retry + 1, 6)
            STOP.wait(min(60, 2 ** retry))
    finally:
        db.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--health", required=True)
    p.add_argument("--log", required=True)
    args = p.parse_args()
    import websocket  # Existing NAS dependency; no import needed for store/tests.
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    # Create/migrate tables before workers; old trades and gaps remain untouched.
    db = store.connect(args.db)
    db.close()
    workers = [threading.Thread(target=consume, args=(websocket, inst, args.db),
                                daemon=True) for inst in STREAMS]
    for worker in workers:
        worker.start()
    try:
        last_export = 0
        while not STOP.wait(5):
            if not all(worker.is_alive() for worker in workers):
                raise RuntimeError("CVD worker exited; inspect journal and collector log")
            if time.monotonic() - last_export >= 60:
                db = store.connect(args.db)
                try:
                    store.export_health(db, args.health)
                finally:
                    db.close()
                last_export = time.monotonic()
    finally:
        STOP.set()
        for worker in workers:
            worker.join(timeout=20)
        db = store.connect(args.db)
        try:
            store.export_health(db, args.health)
        finally:
            db.close()


if __name__ == "__main__":
    main()
