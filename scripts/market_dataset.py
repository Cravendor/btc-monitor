"""Join frozen market signals, macro observations and forward outcomes.

No interpolation, model training or invented market data. Events are attached
only if they were already observed when a signal was issued.
"""
from datetime import datetime, timezone


def _utc(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def build_history(signals, macro_observations, outcomes):
    """Join by signal ID; prevent future macro observations leaking into history."""
    by_id = {}
    for outcome in outcomes:
        key = outcome["prediction_id"]
        if key in by_id:
            raise ValueError("duplicate outcome ID")
        by_id[key] = outcome

    seen = set()
    rows = []
    for signal in signals:
        signal_id = signal["id"]
        if signal_id in seen:
            raise ValueError("duplicate signal ID")
        seen.add(signal_id)
        issued = _utc(signal["issued_at"])
        available_events = []
        for event in macro_observations:
            observed = _utc(event["retrieved_at"])
            if observed <= issued:
                available_events.append({
                    "source_url": event["source_url"],
                    "retrieved_at": observed.isoformat(),
                    "status": event["status"],
                    "event_count": len(event.get("events", []))
                })
        available_events.sort(key=lambda x: (x["retrieved_at"], x["source_url"]))
        result = by_id.get(signal_id)
        if result is not None:
            evaluated = _utc(result["observed_at"]) if result.get("observed_at") else None
            if evaluated and evaluated < issued:
                raise ValueError("outcome precedes signal")
        rows.append({
            "signal_id": signal_id,
            "issued_at": issued.isoformat(),
            "market": signal["market"],
            "timeframe": signal["timeframe"],
            "grade": signal["grade"],
            "model_version": signal["model_version"],
            "macro_as_known_at_issue": available_events,
            "outcome": result or {"status": "unavailable", "reason": "not evaluated"}
        })
    return sorted(rows, key=lambda x: (x["issued_at"], x["signal_id"]))
