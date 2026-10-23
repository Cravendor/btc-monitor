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


def evaluate(records, horizon_hours=24, tolerance_minutes=30):
    """One signal per (timeframe, candle, model); no price interpolation.

    A forward price must come from a candle closing at least the horizon
    after the signal candle, within the specified tolerance. Report only
    directional matches; no trading PNL or causal accuracy claims.
    """
    if horizon_hours <= 0 or tolerance_minutes < 0:
        raise ValueError("invalid evaluation horizon")
    horizon = timedelta(hours=horizon_hours)
    tolerance = timedelta(minutes=tolerance_minutes)
    candles = {tf: {} for tf in TIMEFRAMES}
    signals = {tf: {} for tf in TIMEFRAMES}
    for row in records:
        if not isinstance(row, dict):
            continue
        for tf in TIMEFRAMES:
            s = (row.get("signals") or {}).get(tf) or {}
            if s.get("status") != "ok":
                continue
            stamp = parse_time(s.get("candle_closed_at"))
            value = price(s.get("close_price"))
            if stamp is None or value is None:
                continue
            model = s.get("model_version") or row.get("model_version")
            if not isinstance(model, str) or not model:
                continue
            # Conflicting prices for the same candle invalidate that candle.
            old = candles[tf].get(stamp)
            if old is None:
                candles[tf][stamp] = value
            elif old != value:
                candles[tf][stamp] = -1
            grade = s.get("grade")
            if grade in DIRECTIONS:
                key = (stamp, model)
                previous = signals[tf].get(key)
                candidate = (grade, value)
                if previous is None:
                    signals[tf][key] = candidate
                elif previous != candidate:
                    signals[tf][key] = ("conflict", None)
    result = {}
    for tf in TIMEFRAMES:
        matched = opposed = pending = excluded = 0
        for (stamp, _), (grade, initial) in signals[tf].items():
            if grade not in DIRECTIONS or candles[tf].get(stamp) != initial:
                excluded += 1
                continue
            target = stamp + horizon
            eligible = sorted((t, p) for t, p in candles[tf].items()
                              if target <= t <= target + tolerance and p > 0)
            if not eligible:
                pending += 1
                continue
            change = eligible[0][1] - initial
            if change == 0:
                excluded += 1
            elif change * DIRECTIONS[grade] > 0:
                matched += 1
            else:
                opposed += 1
        result[tf] = {"confirmed_direction": matched, "opposite_direction": opposed,
                      "pending_forward_price": pending, "excluded": excluded,
                      "evaluated": matched + opposed}
    return result


def evaluate_horizons(records, horizons=(1, 4, 24, 168)):
    """Group directional outcomes by timeframe, horizon and original grade."""
    return {hours: evaluate_by_grade(records, hours) for hours in horizons}


def evaluate_by_grade(records, horizon_hours):
    """Reuse the conservative evaluator on grade-filtered signals.

    Preserve all valid candles as possible future prices, while selecting
    only one original grade for outcome counting.
    """
    from copy import deepcopy
    grades = tuple(DIRECTIONS)
    result = {}
    for grade in grades:
        filtered = []
        for record in records:
            if not isinstance(record, dict):
                continue
            item = deepcopy(record)
            for signal in (item.get("signals") or {}).values():
                if isinstance(signal, dict) and signal.get("grade") in DIRECTIONS and signal.get("grade") != grade:
                    signal["grade"] = "neutral"
            filtered.append(item)
        outcome = evaluate(filtered, horizon_hours=horizon_hours)
        for tf, stats in outcome.items():
            result.setdefault(tf, {})[grade] = stats
    return result
