"""Conservative 4H BTC candle-structure scoring (no derivatives inference).

Requires contiguous, closed, valid 4H candles; returns no score when
coverage or candle integrity fails. Does not treat funding/OI as bullish
without a calibrated directional model.
"""
from datetime import datetime, timezone
from math import isfinite
from statistics import mean
from scripts.market_intelligence import Indicator, aggregate

FOUR_HOURS_MS = 4 * 60 * 60 * 1000


def score_closed_4h(candles, as_of, source="Bitget BTCUSDT USDT-FUTURES"):
    now = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if now.tzinfo is None:
        raise ValueError("timezone required")
    now_ms = now.timestamp() * 1000
    parsed = []
    for c in candles:
        try:
            t = int(c["open_time_ms"])
            o, h, l, close, volume = (float(c[k]) for k in
                                     ("open", "high", "low", "close", "base_volume_btc"))
        except (KeyError, ValueError, TypeError):
            return {"status": "unavailable", "reason": "invalid candle", "grade": None}
        if (not all(map(isfinite, (o, h, l, close, volume)))
                or min(o, h, l, close) <= 0 or volume < 0
                or h < max(o, close) or l > min(o, close) or h < l
                or t % FOUR_HOURS_MS != 0):
            return {"status": "unavailable", "reason": "invalid candle geometry", "grade": None}
        if t + FOUR_HOURS_MS <= now_ms:
            parsed.append((t, close, volume))
    parsed.sort()
    if len(parsed) < 24:
        return {"status": "unavailable", "reason": "fewer than 24 closed candles", "grade": None}
    recent = parsed[-24:]
    if any(b[0] - a[0] != FOUR_HOURS_MS for a, b in zip(recent, recent[1:])):
        return {"status": "unavailable", "reason": "non-contiguous 4H candles", "grade": None}
    if now_ms - (recent[-1][0] + FOUR_HOURS_MS) > FOUR_HOURS_MS:
        return {"status": "unavailable", "reason": "stale last closed candle", "grade": None}
    closes = [x[1] for x in recent]
    volumes = [x[2] for x in recent]
    # Independent price trend: last close vs previous 20-candle average.
    baseline = mean(closes[-21:-1])
    delta_pct = (closes[-1] / baseline - 1) * 100
    if delta_pct > 2:
        price_score = 2
    elif delta_pct > 0.5:
        price_score = 1
    elif delta_pct < -2:
        price_score = -2
    elif delta_pct < -0.5:
        price_score = -1
    else:
        price_score = 0
    # Volume is contextual evidence only; its direction is ambiguous.
    volume_ratio = volumes[-1] / mean(volumes[-21:-1]) if mean(volumes[-21:-1]) > 0 else None
    observed_at = datetime.fromtimestamp(
        (recent[-1][0] + FOUR_HOURS_MS) / 1000, timezone.utc).isoformat()
    indicator = Indicator("4h_price_trend", "4h", price_score, "verified", 1,
                          observed_at, source,
                          "Last close relative to preceding 20 closed 4H closes")
    result = aggregate([indicator])
    return {"status": "provisional", "grade": result["label"],
            "score": result["score"], "observed_at": observed_at,
            "price_vs_20_prior_pct": round(delta_pct, 4),
            "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
            "volume_directional_score": None,
            "confidence": "low", "strategy_version": "price_trend_4h_v0.1",
            "reason": "Price-only provisional trend; funding/OI/CVD not scored"}
