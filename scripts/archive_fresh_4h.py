"""Append only fresh, source-validated provisional BTC 4H assessments.

Run as a single writer after data/latest.json is updated. This is not a
validated trading signal and never evaluates macro-bottom hypotheses.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.bitget_market_context import assess_market_context
from scripts.provisional_context_archive import append_context


def run(snapshot, archive, now=None):
    now = now or datetime.now(timezone.utc)
    feed = json.loads(Path(snapshot).read_text(encoding="utf-8"))
    observed = feed.get("updated_at")
    if not observed:
        return {"status": "skipped", "reason": "missing updated_at"}
    stamp = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp > now + timedelta(minutes=5):
        return {"status": "skipped", "reason": "invalid timestamp"}
    if now - stamp > timedelta(hours=5):
        return {"status": "skipped", "reason": "stale snapshot"}
    assessment = assess_market_context(feed, now.isoformat())
    if (assessment.get("status") != "provisional"
            or assessment.get("derivatives_status") != "context_only"):
        return {"status": "skipped", "reason": assessment.get("reason", "ineligible assessment")}
    try:
        changed = append_context(assessment, archive)
    except ValueError as exc:
        if str(exc) == "conflicting observation for existing closed 4H candle":
            return {"status": "skipped", "reason": "conflicting_existing_candle",
                    "observed_at": assessment["observed_at"]}
        raise
    return {"status": "archived" if changed else "unchanged",
            "observed_at": assessment["observed_at"],
            "grade": assessment["grade"], "quality": "provisional_price_only"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m scripts.archive_fresh_4h SNAPSHOT ARCHIVE")
    print(json.dumps(run(sys.argv[1], sys.argv[2]), allow_nan=False))
