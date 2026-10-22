"""Append-only JSONL audit trail for market intelligence snapshots.

Writes locally; never publishes private SQLite trades. Each record carries a
timestamp and version. Consumers should treat it as untrusted until validated.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1


def append_snapshot(path, *, indicators, aggregate_result, hypotheses=None,
                    psychology=None, levels=None, observed_at=None):
    timestamp = observed_at or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include timezone")
    for indicator in indicators:
        indicator.validate()
    if aggregate_result.get("label") is None:
        raise ValueError("aggregate result must contain label")
    record = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": timestamp,
        "indicators": [
            {"name": i.name, "timeframe": i.timeframe, "score": i.score,
             "quality": i.quality, "weight": i.weight,
             "observed_at": i.observed_at, "source": i.source,
             "explanation": i.explanation}
            for i in indicators
        ],
        "aggregate": aggregate_result,
        "hypotheses": hypotheses or {},
        "psychology": psychology or {"phase": "undetermined", "confirmed": False},
        "levels": levels or [],
    }
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, allow_nan=False, ensure_ascii=False, separators=(",", ":")) + "\n"
    # Single local writer is assumed; use a file lock if multiple processes write.
    with dest.open("a", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return record


def read_snapshots(path):
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError("invalid JSONL record at line %s" % number) from exc
