"""Read-only provisional 4H trend assessment from Bitget latest.json.

Uses completed candles only, checks the latest measurement and metric status,
and never turns funding/open interest into directional evidence without a
validated strategy. No signal archive writes or trading.
"""
from datetime import datetime, timezone
from scripts.bitget_signal_bridge import read_latest
from scripts.price_structure_strategy import score_closed_4h


def assess_latest_4h(feed, now):
    bridge = read_latest(feed, now)
    if bridge["status"] != "observed_unscored":
        return {"status": "unavailable", "reason": bridge.get("reason"),
                "grade": None}
    measurement = feed["measurements"][0]
    candles_metric = (measurement.get("metrics") or {}).get("candles_4h") or {}
    if candles_metric.get("status") != "ok":
        return {"status": "unavailable", "reason": "4H candle metric unavailable",
                "grade": None}
    candles = (candles_metric.get("data") or {}).get("candles")
    if not isinstance(candles, list):
        return {"status": "unavailable", "reason": "4H candles missing",
                "grade": None}
    try:
        result = score_closed_4h(candles, now,
                                 source=candles_metric.get("url") or "Bitget")
    except (KeyError, TypeError, ValueError) as error:
        return {"status": "unavailable", "reason": f"invalid 4H data: {error}",
                "grade": None}
    result["exchange"] = "bitget"
    result["market"] = "USDT-FUTURES"
    result["symbol"] = "BTCUSDT"
    result["data_quality"] = "provisional_price_only" if result["status"] == "provisional" else "unavailable"
    return result
