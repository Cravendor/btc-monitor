"""Shared, conservative BTC indicator scoring contract (stdlib only).

This module never fetches market data. Callers must supply validated observations.
Missing or unverified observations are excluded from scoring, not treated as neutral.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

LABELS = {-3: "strongly_bearish", -2: "bearish", -1: "slightly_bearish",
           0: "neutral", 1: "slightly_bullish", 2: "bullish", 3: "strongly_bullish"}
QUALITY = {"verified", "partial", "unverified", "missing", "stale"}
TIMEFRAMES = {"5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"}

@dataclass(frozen=True)
class Indicator:
    name: str
    timeframe: str
    score: Optional[int]
    quality: str
    weight: float
    observed_at: str
    source: str
    explanation: str

    def validate(self):
        if not self.name or self.timeframe not in TIMEFRAMES:
            raise ValueError("invalid indicator name/timeframe")
        if self.quality not in QUALITY:
            raise ValueError("invalid quality")
        if self.score is not None and (type(self.score) is not int or self.score not in LABELS):
            raise ValueError("score must be integer -3..3 or None")
        if self.weight <= 0 or self.weight != self.weight or self.weight == float("inf"):
            raise ValueError("weight must be finite positive")
        if not self.source or not self.explanation:
            raise ValueError("source and explanation required")
        if self.observed_at:
            dt = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("observation time must have timezone")
        if self.quality == "missing" and self.score is not None:
            raise ValueError("missing data cannot have a score")


def aggregate(indicators: Sequence[Indicator], min_coverage: float = 0.75):
    """Return an auditable score. Only verified observations contribute.

    Coverage uses configured weights as denominator; incomplete measurements
    cannot silently inflate confidence. Correlated inputs must be assigned
    non-duplicative weights by the calling strategy.
    """
    if not 0 < min_coverage <= 1:
        raise ValueError("invalid min_coverage")
    if not indicators:
        return {"label": "unavailable", "score": None, "coverage": 0.0,
                "included": [], "excluded": [], "reason": "no indicators"}
    for item in indicators:
        item.validate()
    total = sum(i.weight for i in indicators)
    valid = [i for i in indicators if i.quality == "verified" and i.score is not None]
    excluded = [i.name for i in indicators if i not in valid]
    coverage = sum(i.weight for i in valid) / total
    if coverage < min_coverage:
        return {"label": "unavailable", "score": None, "coverage": round(coverage, 4),
                "included": [i.name for i in valid], "excluded": excluded,
                "reason": "insufficient verified coverage"}
    score = sum(i.score * i.weight for i in valid) / sum(i.weight for i in valid)
    if score <= -2.5:
        label = "strongly_bearish"
    elif score <= -1.5:
        label = "bearish"
    elif score < -0.5:
        label = "slightly_bearish"
    elif score <= 0.5:
        label = "neutral"
    elif score < 1.5:
        label = "slightly_bullish"
    elif score < 2.5:
        label = "bullish"
    else:
        label = "strongly_bullish"
    return {"label": label, "score": round(score, 4),
            "coverage": round(coverage, 4),
            "included": [i.name for i in valid], "excluded": excluded,
            "reason": "provisional weighted indicator score"}
