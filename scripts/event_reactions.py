"""Event-study BTC reactions with strict timestamp and market checks.

Only uses observed, time-stamped prices; does not interpolate or fabricate
missing measurements. Event timestamps must be actual release timestamps,
not unconfirmed FOMC meeting dates.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite


def parse_time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def event_reactions(event, prices, windows_hours=(1, 4, 24), tolerance_minutes=5):
    """Measure return from latest pre-event quote to earliest post-window quote.

    The baseline quote must be within tolerance before the event; end quote
    must be between horizon and horizon+tolerance after release. Each price
    record has market, observed_at, price, and quality='verified'.
    """
    if event.get("verification") != "verified" or not event.get("released_at"):
        return {"status": "unavailable", "reason": "unverified event/release time", "windows": {}}
    release = parse_time(event["released_at"])
    market = event.get("market")
    if not market:
        raise ValueError("market required")
    if tolerance_minutes <= 0:
        raise ValueError("tolerance must be positive")
    observations = []
    for p in prices:
        if p.get("market") != market or p.get("quality") != "verified":
            continue
        value = float(p["price"])
        if not isfinite(value) or value <= 0:
            continue
        observations.append((parse_time(p["observed_at"]), value))
    observations.sort()
    tolerance = timedelta(minutes=tolerance_minutes)
    before = [(t, v) for t, v in observations if release - tolerance <= t <= release]
    if not before:
        return {"status": "unavailable", "reason": "no verified pre-event price", "windows": {}}
    base_time, base_price = before[-1]
    results = {}
    for hours in windows_hours:
        if hours <= 0:
            raise ValueError("window must be positive")
        due = release + timedelta(hours=hours)
        eligible = [(t, v) for t, v in observations if due <= t <= due + tolerance]
        if not eligible:
            results[str(hours)] = {"status": "unavailable", "reason": "missing end price"}
            continue
        end_time, end_price = eligible[0]
        results[str(hours)] = {
            "status": "evaluated", "return_pct": round((end_price / base_price - 1) * 100, 6),
            "baseline_at": base_time.isoformat(), "observed_at": end_time.isoformat()
        }
    return {"status": "evaluated" if any(x["status"] == "evaluated" for x in results.values()) else "unavailable",
            "market": market, "released_at": release.isoformat(), "windows": results}
