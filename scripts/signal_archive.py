"""Append immutable, validated BTC signal history to a JSONL archive.

No synthetic signals. Caller supplies observed signals from a real collector.
Use single-writer execution; concurrent writers require external locking.
"""
import json
from datetime import datetime
from pathlib import Path


GRADES = {"strongly_bearish", "bearish", "slightly_bearish", "neutral",
          "slightly_bullish", "bullish", "strongly_bullish"}
TIMEFRAMES = {"5m", "15m", "30m", "1h", "4h", "1d", "1w"}


def validate_signal(signal):
    required = ("id", "issued_at", "market", "timeframe", "grade",
                "model_version", "source", "quality")
    if not isinstance(signal, dict) or any(not signal.get(k) for k in required):
        raise ValueError("signal missing required provenance")
    if signal["timeframe"] not in TIMEFRAMES or signal["grade"] not in GRADES:
        raise ValueError("unsupported timeframe or grade")
    if signal["quality"] != "verified":
        raise ValueError("only verified signals may be archived as predictions")
    stamp = datetime.fromisoformat(signal["issued_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timezone required")
    return signal


def append_signal(signal, destination):
    """Idempotent single-writer append; return True if newly archived."""
    validate_signal(signal)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if target.exists():
        with target.open(encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    old = json.loads(line)
                    existing.add(old["id"])
    if signal["id"] in existing:
        return False
    serialized = json.dumps(signal, sort_keys=True, ensure_ascii=False, allow_nan=False)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(serialized + "\n")
        stream.flush()
    return True


def export_dataset(archive, output):
    """Export frozen signals with explicitly missing outcome placeholders."""
    source = Path(archive)
    rows = []
    if source.exists():
        with source.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    signal = validate_signal(json.loads(line))
                    rows.append({
                        "signal_id": signal["id"],
                        "issued_at": signal["issued_at"],
                        "market": signal["market"],
                        "timeframe": signal["timeframe"],
                        "grade": signal["grade"],
                        "model_version": signal["model_version"],
                        "outcome": {"status": "unavailable",
                                    "reason": "not yet evaluated"}
                    })
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return len(rows)
