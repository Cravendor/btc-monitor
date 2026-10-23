"""Conservative forward-price evaluation of unique closed-candle BTC signals."""
from datetime import datetime, timedelta, timezone
from math import isfinite

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
DIRECTIONS = {"bullish": 1, "slightly_bullish": 1,
              "bearish": -1, "slightly_bearish": -1}


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo else None
    except ValueError:
        return None


def price(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if isfinite(n) and n > 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def model_version(signal, row):
    """Resolve a recorded model identifier; never infer the current version."""
    value = signal.get("model_version") or row.get("model_version")
    return value if isinstance(value, str) and value.strip() else None


def model_versions(records):
    """Versions with valid stored labels and candle identities, in stable order."""
    versions = set()
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("signals"), dict):
            continue
        observed = parse_time(row.get("updated_at"))
        for tf in TIMEFRAMES:
            signal = row["signals"].get(tf)
            if not isinstance(signal, dict) or signal.get("status") != "ok":
                continue
            closed = parse_time(signal.get("candle_closed_at"))
            model = model_version(signal, row)
            if (model and closed is not None and (observed is None or closed <= observed)
                    and signal.get("grade") in (*DIRECTIONS, "neutral")):
                versions.add(model)
    return sorted(versions)


def evaluate(records, horizon_hours=24, tolerance_minutes=30, *, selected_grade=None, selected_model=None):
    """Count unique signals and mutually exclusive evaluation readiness states.

    The archive's latest aware observation time is the cutoff, never wall-clock
    time: a stopped collector must not turn pending signals into missing prices.
    `pending_forward_price` remains a compatibility subtotal of the four
    forward-price readiness states. No reconstruction or interpolation.
    """
    if horizon_hours <= 0 or tolerance_minutes < 0:
        raise ValueError("invalid evaluation horizon")
    horizon = timedelta(hours=horizon_hours)
    tolerance = timedelta(minutes=tolerance_minutes)
    candles = {tf: {} for tf in TIMEFRAMES}
    signals = {tf: {} for tf in TIMEFRAMES}
    cutoff = None
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("signals"), dict):
            continue
        observed = parse_time(row.get("updated_at"))
        if observed is not None:
            cutoff = max(cutoff, observed) if cutoff else observed
        for tf in TIMEFRAMES:
            signal = row["signals"].get(tf)
            if not isinstance(signal, dict) or signal.get("status") != "ok":
                continue
            stamp = parse_time(signal.get("candle_closed_at"))
            if stamp is None or (observed is not None and stamp > observed):
                continue
            value = price(signal.get("close_price"))
            if value is not None:
                candles[tf].setdefault(stamp, set()).add(value)
            model = model_version(signal, row)
            grade = signal.get("grade")
            if grade not in DIRECTIONS or not isinstance(model, str) or not model:
                continue
            candidate = signals[tf].setdefault((stamp, model),
                                               {"grades": set(), "prices": set()})
            candidate["grades"].add(grade)
            if value is not None:
                candidate["prices"].add(value)
    periods = dict(zip(TIMEFRAMES, (300, 900, 1800, 3600, 14400, 86400, 604800)))
    result = {}
    for tf in TIMEFRAMES:
        counts = {key: 0 for key in (
            "confirmed_direction", "opposite_direction", "awaiting_horizon",
            "awaiting_price_window", "missing_forward_price", "unknown_observation_time",
            "missing_initial_price", "unsupported_horizon", "excluded", "total_signals")}
        # A same-timeframe candle cannot resolve a shorter, misaligned horizon
        # unless the next close falls within the explicitly allowed tolerance.
        remainder = horizon.total_seconds() % periods[tf]
        unsupported = bool(remainder and periods[tf] - remainder > tolerance.total_seconds())
        for (stamp, model), candidate in signals[tf].items():
            if selected_model is not None and model != selected_model:
                continue
            grades, values = candidate["grades"], candidate["prices"]
            if selected_grade is not None and selected_grade not in grades:
                continue
            counts["total_signals"] += 1
            if len(grades) != 1 or len(values) > 1 or len(candles[tf].get(stamp, ())) > 1:
                counts["excluded"] += 1
                continue
            if unsupported:
                counts["unsupported_horizon"] += 1
                continue
            if not values:
                counts["missing_initial_price"] += 1
                continue
            initial = next(iter(values))
            grade = next(iter(grades))
            target = stamp + horizon
            eligible = sorted((t, next(iter(prices))) for t, prices in candles[tf].items()
                              if target <= t <= target + tolerance and len(prices) == 1)
            if not eligible:
                state = ("unknown_observation_time" if cutoff is None else
                         "awaiting_horizon" if cutoff < target else
                         "awaiting_price_window" if cutoff <= target + tolerance else
                         "missing_forward_price")
                counts[state] += 1
                continue
            change = eligible[0][1] - initial
            if change == 0:
                counts["excluded"] += 1
            else:
                counts["confirmed_direction" if change * DIRECTIONS[grade] > 0
                       else "opposite_direction"] += 1
        counts["evaluated"] = counts["confirmed_direction"] + counts["opposite_direction"]
        counts["pending_forward_price"] = sum(counts[k] for k in (
            "awaiting_horizon", "awaiting_price_window", "missing_forward_price",
            "unknown_observation_time"))
        result[tf] = counts
    return result


def evaluate_horizons(records, horizons=(1, 4, 24, 168), *, selected_model=None):
    """Group directional outcomes by timeframe, horizon and original grade."""
    return {hours: evaluate_by_grade(records, hours, selected_model=selected_model) for hours in horizons}


def evaluate_by_grade(records, horizon_hours, *, selected_model=None):
    """Filter candidates after conflict detection, retaining all forward prices.

    A conflicting signal contributes an exclusion to every affected original
    grade; grade groups must therefore not be summed as independent totals.
    """
    result = {}
    for grade in DIRECTIONS:
        outcome = evaluate(records, horizon_hours=horizon_hours, selected_grade=grade, selected_model=selected_model)
        for tf, stats in outcome.items():
            result.setdefault(tf, {})[grade] = stats
    return result


def evaluate_models(records, horizons=(1, 4, 24, 168)):
    """Isolated model sample groups, preserving candles and conflicts globally."""
    return {model: evaluate_horizons(records, horizons, selected_model=model)
            for model in model_versions(records)}
