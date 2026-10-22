"""Auditable economic event records. No live data is fetched here."""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Optional


def parse_utc(value):
    if not value:
        raise ValueError("timestamp required")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class MacroEvent:
    event_id: str
    category: str
    scheduled_at: str
    source_url: str
    retrieved_at: str
    actual: Optional[float] = None
    consensus: Optional[float] = None
    previous: Optional[float] = None
    unit: str = ""
    released_at: Optional[str] = None
    consensus_source_url: str = ""
    revision: Optional[float] = None

    def validate(self):
        if not self.event_id or not self.category or not self.source_url.startswith("https://"):
            raise ValueError("event identity, category and HTTPS source required")
        scheduled, retrieved = parse_utc(self.scheduled_at), parse_utc(self.retrieved_at)
        if self.released_at:
            released = parse_utc(self.released_at)
            if retrieved < released:
                raise ValueError("retrieved before release")
        elif self.actual is not None:
            raise ValueError("actual without release timestamp")
        for value in (self.actual, self.consensus, self.previous, self.revision):
            if value is not None and (isinstance(value, bool) or not isfinite(float(value))):
                raise ValueError("invalid numeric observation")
        if self.consensus is not None and not self.consensus_source_url.startswith("https://"):
            raise ValueError("consensus requires verifiable source")
        return scheduled

    def as_of(self, timestamp):
        """Only expose actual figures if release occurred by the evaluation cutoff.

        Caller must provide an archival observation obtained by the cutoff.
        A current revised release cannot be backfilled into past predictions.
        """
        self.validate()
        cutoff = parse_utc(timestamp)
        if parse_utc(self.retrieved_at) > cutoff:
            return {"status": "unavailable", "reason": "not observed by cutoff"}
        if self.actual is None or parse_utc(self.released_at) > cutoff:
            return {"status": "scheduled", "surprise": None}
        if self.consensus is None:
            return {"status": "released", "surprise": None}
        return {"status": "released", "surprise": self.actual - self.consensus,
                "unit": self.unit, "direction": "above" if self.actual > self.consensus
                else "below" if self.actual < self.consensus else "inline"}
