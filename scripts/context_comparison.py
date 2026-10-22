"""Compare sequential archived Bitget market-context assessments.

Only compares like-for-like source, timeframe and strategy. Never interprets
missing data as zero or invents a change in bull/bear conviction.
"""
from datetime import datetime, timezone

GRADES = {"strongly_bearish": -3, "bearish": -2, "slightly_bearish": -1,
          "neutral": 0, "slightly_bullish": 1, "bullish": 2,
          "strongly_bullish": 3}


def _dt(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timezone required")
    return t.astimezone(timezone.utc)


def compare_context(current, previous):
    for record in (current, previous):
        if record.get("status") != "provisional" or record.get("grade") not in GRADES:
            return {"status": "unavailable", "reason": "missing provisional assessment"}
        if record.get("source") != "Bitget USDT-FUTURES BTCUSDT latest.json":
            return {"status": "unavailable", "reason": "source mismatch"}
    if _dt(current["observed_at"]) <= _dt(previous["observed_at"]):
        return {"status": "unavailable", "reason": "non-increasing closed candle time"}
    old, new = GRADES[previous["grade"]], GRADES[current["grade"]]
    change = new - old
    return {
        "status": "compared", "previous_grade": previous["grade"],
        "current_grade": current["grade"], "grade_step_change": change,
        "trend": "more_bullish" if change > 0 else "more_bearish" if change < 0 else "unchanged",
        "previous_at": previous["observed_at"], "current_at": current["observed_at"],
        "confidence": "low",
        "caution": "Price-only provisional grades; not macro-cycle confirmation"
    }
