"""Read-only archival snapshot for macro calendar source observations.

Records source observations with provenance; unconfirmed parser output is never
promoted to a verified economic event. One JSON per content fingerprint avoids
duplicate archives when the same source is collected repeatedly.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path


def archive_source_snapshot(snapshot, root):
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    required = ("source_url", "retrieved_at", "status", "events")
    if any(k not in snapshot for k in required):
        raise ValueError("incomplete snapshot")
    if not snapshot["source_url"].startswith("https://"):
        raise ValueError("HTTPS provenance required")
    timestamp = datetime.fromisoformat(snapshot["retrieved_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("timezone required")
    if snapshot["status"] != "parsed_unconfirmed":
        raise ValueError("unexpected source validation status")
    if not isinstance(snapshot["events"], list):
        raise ValueError("events must be a list")
    for event in snapshot["events"]:
        if event.get("verification") != "parsed_unconfirmed":
            raise ValueError("archive cannot claim verified events")
    serialized = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, allow_nan=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:20]
    folder = Path(root) / timestamp.strftime("%Y/%m/%d")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ("fomc-" + digest + ".json")
    if not target.exists():
        with target.open("x", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
    return str(target)
