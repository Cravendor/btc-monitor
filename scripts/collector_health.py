"""Independent freshness check of persisted BTC snapshots; no network/API calls."""
import json
from datetime import datetime, timezone
from pathlib import Path

MAX_AGE_SECONDS = 3600


def check(records, now):
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    valid = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("signals"), dict):
            continue
        try:
            stamp = datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                continue
            stamp = stamp.astimezone(timezone.utc)
            if stamp <= now:
                valid.append(stamp)
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
    latest = max(valid) if valid else None
    age = (now - latest).total_seconds() if latest else None
    return {
        "schema_version": 1,
        "checked_at": now.isoformat(),
        "last_snapshot_at": latest.isoformat() if latest else None,
        "age_seconds": round(age) if age is not None else None,
        "max_age_seconds": MAX_AGE_SECONDS,
        "status": "missing" if latest is None else ("stale" if age > MAX_AGE_SECONDS else "current"),
    }


def run(source="data/history/timeframe_signals.jsonl", target="data/collector-health.json"):
    records = []
    path = Path(source)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except (ValueError, TypeError):
                continue
    report = check(records, datetime.now(timezone.utc))
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    run()
