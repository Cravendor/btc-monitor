"""Read-only bridge from Bitget latest.json to validated scoring inputs.

Does not fabricate Bull/Bear grades from prices. Only emits observations
with their original provenance and quality; a separate, versioned strategy
must score them before archival.
"""
from datetime import datetime, timezone
from math import isfinite


def _timestamp(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def read_latest(feed, now, max_age_hours=5):
    if (feed.get("exchange"), feed.get("market"), feed.get("symbol")) != (
        "bitget", "USDT-FUTURES", "BTCUSDT"
    ):
        raise ValueError("unexpected exchange/market/symbol")
    current = _timestamp(now)
    measurements = feed.get("measurements") or []
    if not measurements:
        return {"status": "unavailable", "reason": "no measurements", "observations": []}
    measurement = measurements[0]
    if measurement.get("status") != "ok":
        return {"status": "unavailable", "reason": "latest measurement not ok", "observations": []}
    measured = _timestamp(measurement["finished_at"])
    age = (current - measured).total_seconds()
    if age < 0 or age > max_age_hours * 3600:
        return {"status": "stale", "reason": "measurement outside freshness window",
                "observed_at": measured.isoformat(), "observations": []}
    metrics = measurement.get("metrics") or {}
    observations = []
    for name, field in (("futures_price", "lastPr"), ("funding", "fundingRate"),
                        ("open_interest", "holdingAmount")):
        metric = metrics.get(name) or {}
        data = metric.get("data") or {}
        if metric.get("status") != "ok" or field not in data:
            continue
        try:
            value = float(data[field])
            timestamp = _timestamp(metric["observed_at"])
        except (ValueError, TypeError, KeyError):
            continue
        if not isfinite(value) or (name != "funding" and value <= 0):
            continue
        if timestamp > current or abs((timestamp - measured).total_seconds()) > 300:
            continue
        observations.append({"name": name, "value": value,
                             "observed_at": timestamp.isoformat(),
                             "source": metric.get("url"),
                             "quality": "verified_source_status_only"})
    return {"status": "observed_unscored", "market": "bitget_USDT-FUTURES_BTCUSDT",
            "observed_at": measured.isoformat(), "observations": observations,
            "grade": None, "reason": "no validated scoring strategy applied"}
