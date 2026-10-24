#!/usr/bin/env python3
"""Validate and append a manually supplied monitor report; no fabricated scores."""
import datetime as dt
import json
import os
import pathlib
import sys

LABELS = {-2: "sterk bearish", -1: "zwak bearish", 0: "neutraal", 1: "zwak bullish", 2: "sterk bullish"}
MONITORS = {"daily", "4h-warning", "market-risk"}
HORIZONS = ("4h_1d", "7d", "30d_macro")

def validate(obj):
    if isinstance(obj, dict) and obj.get("schema_version") == 2:
        if __package__:
            from .monitor_archive import validate_record
        else:
            from monitor_archive import validate_record
        return validate_record(obj)
    if not isinstance(obj, dict) or obj.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")
    if obj.get("monitor") not in MONITORS:
        raise ValueError("Unknown monitor")
    try:
        ts = dt.datetime.fromisoformat(obj["reported_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("reported_at must be ISO8601 with timezone") from exc
    if ts.tzinfo is None:
        raise ValueError("reported_at must have a timezone")
    if ts > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10):
        raise ValueError("Future report time")
    bias = obj.get("bias")
    if not isinstance(bias, dict) or set(bias) != set(HORIZONS):
        raise ValueError("bias must contain 4h_1d, 7d, 30d_macro")
    for horizon, entry in bias.items():
        if not isinstance(entry, dict):
            raise ValueError("Invalid horizon: " + horizon)
        score = entry.get("score")
        if score is not None and (type(score) is not int or score not in LABELS):
            raise ValueError("Invalid score: " + horizon)
        if score is None and entry.get("status") != "ONVOLDOENDE DATA":
            raise ValueError("Missing score requires ONVOLDOENDE DATA")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError("Reason required for " + horizon)
    sources = obj.get("sources")
    if not isinstance(sources, list) or not sources or not all(isinstance(s, str) and s.startswith("https://") for s in sources):
        raise ValueError("At least one HTTPS source URL required")
    return ts.astimezone(dt.timezone.utc)

def main():
    raw = os.environ.get("REPORT_JSON", "")
    if not raw or len(raw) > 20000:
        raise ValueError("REPORT_JSON missing or too long")
    obj = json.loads(raw)
    ts = validate(obj)
    date = ts.strftime("%Y/%m/%d")
    path = pathlib.Path("reports") / date / (obj["monitor"] + "-" + ts.strftime("%H%M%S") + ".json")
    if path.exists():
        raise ValueError("Report already exists; never overwrite historical results")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if __package__:
        from .monitor_archive import import_inbox
    else:
        from monitor_archive import import_inbox
    import_inbox()
    print("Saved", path)

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        print("Report rejected:", error, file=sys.stderr)
        sys.exit(1)
