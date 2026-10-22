"""Conservative, read-only provisional BTC price trend across candle intervals.

Input candles must be native, complete, consecutive candles for the requested
timeframe. No resampling 4H candles into shorter timeframes, no derivatives
inference, and no live orders.
"""
from datetime import datetime, timezone
from math import isfinite
from statistics import mean

INTERVAL_MS = {"5m": 300_000, "15m": 900_000, "30m": 1_800_000,
               "1h": 3_600_000, "4h": 14_400_000,
               "1d": 86_400_000, "1w": 604_800_000}
GRADES = {-2: "bearish", -1: "slightly_bearish", 0: "neutral",
          1: "slightly_bullish", 2: "bullish"}


def assess(candles, timeframe, as_of):
    if timeframe not in INTERVAL_MS:
        raise ValueError("unsupported timeframe")
    period = INTERVAL_MS[timeframe]
    now = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if now.tzinfo is None:
        raise ValueError("timezone required")
    offset = 4 * 86400000 if timeframe == "1w" else 0
    parsed = []
    for candle in candles:
        try:
            t = int(candle["open_time_ms"])
            o, h, l, c, v = [float(candle[k]) for k in
                             ("open", "high", "low", "close", "base_volume_btc")]
        except (TypeError, ValueError, KeyError):
            return {"status": "unavailable", "reason": "invalid candle"}
        if (not all(isfinite(n) for n in (o, h, l, c, v))
                or min(o, h, l, c) <= 0 or v < 0 or
                h < max(o, c) or l > min(o, c) or (t - offset) % period != 0):
            return {"status": "unavailable", "reason": "invalid candle geometry"}
        if t + period <= now.timestamp() * 1000:
            parsed.append((t, c, v))
    parsed.sort()
    recent = parsed[-24:]
    if len(recent) != 24:
        return {"status": "unavailable", "reason": "fewer than 24 closed candles"}
    if any(b[0] - a[0] != period for a, b in zip(recent, recent[1:])):
        return {"status": "unavailable", "reason": "non-contiguous candles"}
    if now.timestamp() * 1000 - (recent[-1][0] + period) > period:
        return {"status": "unavailable", "reason": "stale closed candle"}
    closes = [x[1] for x in recent]
    volumes = [x[2] for x in recent]
    baseline = mean(closes[-21:-1])
    delta = (closes[-1] / baseline - 1) * 100
    # Independent, transparent evidence: 20-bar price trend, 6-bar
    # momentum and relative volume. Volume alone never sets direction.
    momentum_6_pct = (closes[-1] / closes[-7] - 1) * 100
    avg_volume = mean(volumes[-21:-1])
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else None
    trend_vote = 1 if delta > 0.5 else -1 if delta < -0.5 else 0
    momentum_vote = 1 if momentum_6_pct > 0.5 else -1 if momentum_6_pct < -0.5 else 0
    agreement = trend_vote != 0 and trend_vote == momentum_vote
    if agreement:
        evidence_state = "aligned"
    elif trend_vote != 0 and momentum_vote != 0:
        evidence_state = "conflicting"
    elif trend_vote == 0 and momentum_vote == 0:
        evidence_state = "no_direction"
    else:
        evidence_state = "partial_direction"
    # Two agreeing directional measures are needed for a directional label.
    # Strong labels require a large price displacement AND elevated volume.
    if agreement:
        direction = trend_vote
        strong = abs(delta) > 2 and volume_ratio is not None and volume_ratio >= 1.2
        score = direction * (2 if strong else 1)
    else:
        score = 0
    return {"status": "provisional", "timeframe": timeframe,
            "grade": GRADES[score], "score": score,
            "observed_at": datetime.fromtimestamp((recent[-1][0] + period) / 1000, timezone.utc).isoformat(),
            "price_vs_20_prior_pct": round(delta, 4),
            "momentum_6_pct": round(momentum_6_pct, 4),
            "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
            "evidence": {"trend_vote": trend_vote, "momentum_vote": momentum_vote,
                         "directional_agreement": agreement, "state": evidence_state, "elevated_volume": bool(volume_ratio is not None and volume_ratio >= 1.2)},
            "confidence": "low", "quality": "provisional_price_volume_only",
            "cvd_status": "unavailable", "model_version": "multi_tf_evidence_v0.2",
            "note": "Heuristic uncalibrated labels; no CVD, orderflow or backtested confidence"}
