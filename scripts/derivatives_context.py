"""Derivatives context, never a stand-alone bullish/bearish prediction.

Funding is a crowding proxy; OI needs a prior comparable observation before
a change can be interpreted. Both remain non-directional in this module.
"""
from datetime import datetime, timezone
from math import isfinite


def _time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc)


def derivatives_context(current, previous=None, max_gap_hours=8):
    required = ("market", "observed_at", "funding_rate", "open_interest")
    if any(k not in current for k in required):
        return {"status": "unavailable", "reason": "missing current fields"}
    now = _time(current["observed_at"])
    funding, oi = float(current["funding_rate"]), float(current["open_interest"])
    if not isfinite(funding) or not isfinite(oi) or oi <= 0:
        return {"status": "unavailable", "reason": "invalid current values"}
    result = {"status": "context_only", "market": current["market"],
              "observed_at": now.isoformat(), "funding_rate": funding,
              "open_interest": oi, "oi_change_pct": None,
              "directional_grade": None,
              "interpretation": "Funding is positioning context, not direction"}
    if previous is None:
        result["reason"] = "no comparable prior open interest"
        return result
    if previous.get("market") != current["market"]:
        result["reason"] = "previous market differs"
        return result
    before = _time(previous["observed_at"])
    elapsed = (now - before).total_seconds()
    old = float(previous["open_interest"])
    if not isfinite(old) or old <= 0 or not 0 < elapsed <= max_gap_hours * 3600:
        result["reason"] = "invalid prior OI or comparison interval"
        return result
    result["oi_change_pct"] = round((oi / old - 1) * 100, 6)
    result["comparison_at"] = before.isoformat()
    result["reason"] = "OI change is descriptive, not directional confirmation"
    return result
