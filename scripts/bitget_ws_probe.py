"""Bounded, read-only connectivity probe for Bitget classic public trade feeds.

No orders, API keys, CVD calculations, or persistent background process.
Python 3.8 compatible; requires websocket-client 1.8.0.
"""
import json
import sys
import time
from datetime import datetime, timezone

import websocket

URL = "wss://ws.bitget.com/v2/ws/public"
MARKETS = ("SPOT", "USDT-FUTURES")

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def main():
    for market in MARKETS:
        print(json.dumps({"time_utc": utc_now(), "market": market, "state": "connecting"}), flush=True)
        ws = None
        try:
            ws = websocket.create_connection(URL, timeout=10, enable_multithread=True)
            ws.settimeout(8)
            ws.send(json.dumps({"op": "subscribe", "args": [
                {"instType": market, "channel": "trade", "instId": "BTCUSDT"}
            ]}))
            deadline = time.monotonic() + 25
            count = 0
            while time.monotonic() < deadline and count < 3:
                try:
                    raw = ws.recv()
                except websocket.WebSocketTimeoutException:
                    ws.send("ping")
                    continue
                if isinstance(raw, bytes):
                    print(json.dumps({"time_utc": utc_now(), "market": market,
                                      "state": "binary_frame", "bytes": len(raw)}), flush=True)
                    continue
                if raw == "pong":
                    continue
                try:
                    obj = json.loads(raw)
                except ValueError:
                    print(json.dumps({"time_utc": utc_now(), "market": market,
                                      "state": "unrecognized_frame"}), flush=True)
                    continue
                # Print schema only; avoid dumping market payloads into task logs.
                data = obj.get("data")
                sample = data[0] if isinstance(data, list) and data else None
                print(json.dumps({"time_utc": utc_now(), "market": market,
                                  "event": obj.get("event"), "code": obj.get("code"),
                                  "msg": obj.get("msg"), "action": obj.get("action"),
                                  "data_count": len(data) if isinstance(data, list) else None,
                                  "sample_type": type(sample).__name__ if sample is not None else None,
                                  "sample_keys": sorted(sample.keys()) if isinstance(sample, dict) else None,
                                  "sample_length": len(sample) if isinstance(sample, list) else None}), flush=True)
                count += 1
        except Exception as exc:
            print(json.dumps({"time_utc": utc_now(), "market": market,
                              "state": "error", "error_type": type(exc).__name__,
                              "message": str(exc)[:250]}), flush=True)
        finally:
            if ws is not None:
                ws.close()

if __name__ == "__main__":
    main()
