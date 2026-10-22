"""Build a read-only 4H BTC market context preview from real Bitget snapshots.

Price scores are provisional. Funding/OI are context only, never used to
silently promote a grade or confirm macro-bottom/distribution hypotheses.
"""
from datetime import datetime, timezone
from math import isfinite
from scripts.bitget_4h_assessment import assess_latest_4h
from scripts.derivatives_context import derivatives_context
from scripts.market_context_report import combine_context


def _time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def _derivatives_measurement(measurement, market):
    metrics = measurement.get("metrics") or {}
    values = {}
    for name, field in (("funding", "fundingRate"), ("open_interest", "holdingAmount")):
        entry = metrics.get(name) or {}
        if entry.get("status") != "ok":
            return None
        try:
            number = float(entry["data"][field])
            observed = _time(entry["observed_at"])
        except (KeyError, TypeError, ValueError):
            return None
        if not isfinite(number) or (name == "open_interest" and number <= 0):
            return None
        values[name] = number
        values[name + "_at"] = observed
    if abs((values["funding_at"] - values["open_interest_at"]).total_seconds()) > 300:
        return None
    finished = _time(measurement["finished_at"])
    if max(abs((finished - values[k]).total_seconds())
           for k in ("funding_at", "open_interest_at")) > 300:
        return None
    return {"market": market, "observed_at": finished.isoformat(),
            "funding_rate": values["funding"],
            "open_interest": values["open_interest"]}


def assess_market_context(feed, now):
    price = assess_latest_4h(feed, now)
    if price.get("status") != "provisional":
        return combine_context(price)
    market = "bitget_USDT-FUTURES_BTCUSDT"
    measurements = feed.get("measurements") or []
    current = _derivatives_measurement(measurements[0], market)
    if current is None:
        return combine_context(price)
    previous = None
    for candidate in measurements[1:]:
        try:
            if candidate.get("status") != "ok":
                continue
            earlier = _derivatives_measurement(candidate, market)
            if earlier and _time(earlier["observed_at"]) < _time(current["observed_at"]):
                previous = earlier
                break
        except (KeyError, TypeError, ValueError):
            continue
    context = derivatives_context(current, previous)
    result = combine_context(price, context)
    result["observed_at"] = price.get("observed_at")
    result["derivatives_observed_at"] = current["observed_at"]
    result["source"] = "Bitget USDT-FUTURES BTCUSDT latest.json"
    return result
