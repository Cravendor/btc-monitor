"""Forward-only outcome evaluation; no training or automatic model changes.

Predictions must be frozen before outcomes become available. Each evaluation
uses prices from the same market and a timestamp at/after the due time.
"""
from datetime import datetime, timedelta


def _time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include timezone")
    return parsed


def evaluate_direction(prediction, outcome, *, tolerance_seconds=300):
    """Evaluate a directional hypothesis without using future data at issuance.

    prediction: id, issued_at, horizon_hours, market, entry_price,
                direction ('bull' or 'bear'), model_version
    outcome: observed_at, market, price
    Neutral or structural confirmations require their own separate validators.
    """
    required = ("id", "issued_at", "horizon_hours", "market", "entry_price",
                "direction", "model_version")
    if any(k not in prediction for k in required):
        raise ValueError("incomplete prediction")
    if prediction["direction"] not in ("bull", "bear"):
        raise ValueError("unsupported direction")
    if prediction["market"] != outcome.get("market"):
        raise ValueError("different market")
    issued = _time(prediction["issued_at"])
    observed = _time(outcome["observed_at"])
    horizon = float(prediction["horizon_hours"])
    if not 0 < horizon <= 24 * 365:
        raise ValueError("invalid horizon")
    due = issued + timedelta(hours=horizon)
    if not due <= observed <= due + timedelta(seconds=tolerance_seconds):
        return {"status": "unavailable", "reason": "no price within evaluation window"}
    entry, exit_price = float(prediction["entry_price"]), float(outcome["price"])
    if not 0 < entry < float("inf") or not 0 < exit_price < float("inf"):
        raise ValueError("prices must be finite positive")
    change = (exit_price / entry - 1) * 100
    if change == 0:
        verdict = "flat"
    else:
        verdict = "correct" if (change > 0) == (prediction["direction"] == "bull") else "incorrect"
    return {"status": "evaluated", "prediction_id": prediction["id"],
            "model_version": prediction["model_version"], "due_at": due.isoformat(),
            "observed_at": observed.isoformat(), "return_pct": round(change, 6),
            "verdict": verdict}
