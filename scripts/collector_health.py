"""Independent freshness check of persisted BTC snapshots; no network/API calls."""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.history_coverage import coverage, observations

MAX_AGE_SECONDS = 3600
EXPECTED_INTERVAL_SECONDS = 1800
COVERAGE_WINDOW_HOURS = 24


def check(records, now):
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    valid = observations(records, now)
    latest = valid[-1][0] if valid else None
    age = (now - latest).total_seconds() if latest else None
    return {
        "schema_version": 3,
        "coverage_24h": coverage(records, now),
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
    from scripts.analysis_quality import review
    try:
        feed = json.loads(Path('data/latest.json').read_text())
    except (OSError, ValueError):
        feed = {}
    report['analysis_quality'] = review(feed, report['checked_at'])
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    run()
