"""Compare archived provisional BTC 4H grades over rolling 24h/7d/30d windows.

Never manufacture missing history. Window changes require a prior valid
observation close to the target boundary, and comparable model/source.
"""
from datetime import datetime, timezone, timedelta

GRADES = {"strongly_bearish": -3, "bearish": -2, "slightly_bearish": -1,
          "neutral": 0, "slightly_bullish": 1, "bullish": 2,
          "strongly_bullish": 3}
WINDOWS = {"24h": timedelta(hours=24), "7d": timedelta(days=7),
           "30d": timedelta(days=30)}
SOURCE = "Bitget USDT-FUTURES BTCUSDT latest.json"


def _time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timezone required")
    return stamp.astimezone(timezone.utc)


def trend_windows(records, as_of, tolerance_hours=4):
    now = _time(as_of)
    eligible = []
    seen = set()
    for record in records:
        if (record.get("quality") != "provisional_price_only"
                or record.get("source") != SOURCE
                or record.get("grade") not in GRADES):
            continue
        stamp = _time(record["observed_at"])
        if stamp > now:
            continue
        key = (record.get("model_version"), stamp)
        if key in seen:
            raise ValueError("duplicate candle in history")
        seen.add(key)
        eligible.append((stamp, record))
    eligible.sort(key=lambda x: x[0])
    if not eligible:
        return {"status": "unavailable", "reason": "no eligible observations", "windows": {}}
    latest_at, latest = eligible[-1]
    if now - latest_at > timedelta(hours=tolerance_hours):
        return {"status": "unavailable", "reason": "latest observation stale", "windows": {}}
    results = {}
    for label, span in WINDOWS.items():
        target = latest_at - span
        matches = [(stamp, record) for stamp, record in eligible
                   if record.get("model_version") == latest.get("model_version")
                   and target - timedelta(hours=tolerance_hours) <= stamp <= target]
        if not matches:
            results[label] = {"status": "unavailable", "reason": "missing baseline near window boundary"}
            continue
        old_at, old = matches[-1]
        change = GRADES[latest["grade"]] - GRADES[old["grade"]]
        results[label] = {
            "status": "compared", "previous_grade": old["grade"],
            "current_grade": latest["grade"], "grade_step_change": change,
            "trend": "more_bullish" if change > 0 else "more_bearish" if change < 0 else "unchanged",
            "baseline_at": old_at.isoformat(), "latest_at": latest_at.isoformat(),
            "confidence": "low"
        }
    return {"status": "provisional", "current_grade": latest["grade"],
            "model_version": latest.get("model_version"), "latest_at": latest_at.isoformat(),
            "windows": results, "caution": "Price-only historical grades, not confirmed market direction"}
