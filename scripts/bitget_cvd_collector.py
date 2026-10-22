"""Preview-only dual-stream Bitget trade journal for Python 3.8.

Requires websocket-client. Stores observed trades, NEVER claims complete CVD.
"""
import argparse
import json
import logging
import signal
import threading
import time
import websocket

try:
    from scripts.cvd_store import connect, record_gap, record_trade, export_health
except ImportError:
    from cvd_store import connect, record_gap, record_trade, export_health

URL = "wss://ws.bitget.com/v2/ws/public"
STREAMS = {"SPOT": "spot", "USDT-FUTURES": "usdt_futures"}
STOP = threading.Event()

def now_ms():
    return int(time.time() * 1000)

def consume(inst, path):
    market = STREAMS[inst]
    db = connect(path)
    retry = 0
    while not STOP.is_set():
        ws = None
        record_gap(db, market=market, start_ms=now_ms(),
                   reason="start/reconnect; historical coverage unverified")
        try:
            ws = websocket.create_connection(URL, timeout=15, enable_multithread=True)
            ws.settimeout(10)
            ws.send(json.dumps({"op": "subscribe", "args": [
                {"instType": inst, "channel": "trade", "instId": "BTCUSDT"}]}))
            retry = 0
            last_frame = time.monotonic()
            last_ping = last_frame
            logging.info("%s connected", market)
            while not STOP.is_set():
                try:
                    raw = ws.recv()
                except websocket.WebSocketTimeoutException:
                    if time.monotonic() - last_frame > 35:
                        raise TimeoutError("no inbound frames")
                    if time.monotonic() - last_ping > 20:
                        ws.send("ping")
                        last_ping = time.monotonic()
                    continue
                last_frame = time.monotonic()
                if raw == "pong":
                    continue
                if not isinstance(raw, str):
                    raise ValueError("unexpected binary frame")
                obj = json.loads(raw)
                if obj.get("event") == "error":
                    raise RuntimeError("subscription error: " + str(obj.get("msg")))
                if obj.get("event") == "subscribe":
                    continue
                if obj.get("arg", {}).get("channel") != "trade":
                    continue
                if obj.get("action") not in ("snapshot", "update"):
                    continue
                for trade in obj.get("data", []):
                    try:
                        if trade["side"] not in ("buy", "sell"):
                            raise ValueError("invalid side")
                        record_trade(db, market=market, trade_id=trade["tradeId"],
                                     ts_ms=int(trade["ts"]), received_ms=now_ms(),
                                     price=trade["price"], size_btc=trade["size"],
                                     taker_side=trade["side"])
                    except (ValueError, KeyError, TypeError, OverflowError):
                        record_gap(db, market=market, start_ms=now_ms(),
                                   reason="invalid trade; completeness unverified")
        except Exception as exc:
            logging.warning("%s disconnected: %s", market, str(exc)[:180])
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass
        retry += 1
        STOP.wait(min(60, 2 ** min(retry, 6)))
    db.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--health", required=True)
    p.add_argument("--log", required=True)
    args = p.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    workers = [threading.Thread(target=consume, args=(inst, args.db),
                                daemon=True) for inst in STREAMS]
    for worker in workers:
        worker.start()
    try:
        while not STOP.wait(60):
            db = connect(args.db)
            try:
                export_health(db, args.health)
            finally:
                db.close()
    finally:
        STOP.set()
        for worker in workers:
            worker.join(timeout=20)
        db = connect(args.db)
        try:
            export_health(db, args.health)
        finally:
            db.close()

if __name__ == "__main__":
    main()
