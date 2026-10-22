"""Append-only read-only signal snapshots for longitudinal comparisons."""
import json
from math import isfinite
from pathlib import Path

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
GRADES = {"bearish", "slightly_bearish", "neutral", "slightly_bullish", "bullish"}


def record_health(health, destination="data/history/timeframe_signals.jsonl"):
    if health.get("exchange") != "bitget" or health.get("market") != "USDT-FUTURES" or health.get("symbol") != "BTCUSDT":
        raise ValueError("unexpected market identity")
    timestamp = health.get("updated_at")
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError("missing observation timestamp")
    signals = {}
    def safe_price(value):
        try:
            price = float(value)
            return price if isfinite(price) and price > 0 else None
        except (TypeError, ValueError, OverflowError):
            return None

    for tf in TIMEFRAMES:
        item = health.get("timeframes", {}).get(tf, {})
        grade = item.get("grade") if item.get("status") == "ok" and item.get("signal_status") == "provisional" else None
        signals[tf] = {
            "grade": grade if grade in GRADES else None,
            "status": "ok" if grade in GRADES else "unavailable",
            "candle_closed_at": item.get("observed_at") if grade in GRADES else None,
            "close_price": safe_price(item.get("candle_close_price")) if grade in GRADES else None,
            "model_version": item.get("model_version") if grade in GRADES else None,
            "evidence_state": item.get("evidence_state") if grade in GRADES else None,
        }
    entry = {"updated_at": timestamp, "model_version": "multi_tf_evidence_v0.2", "signals": signals}
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    # Idempotent across repeated GitHub Actions runs for the same snapshot.
    if any(json.loads(line).get("updated_at") == timestamp for line in existing if line.strip()):
        return entry
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":"), allow_nan=False) + "\n")
    return entry
