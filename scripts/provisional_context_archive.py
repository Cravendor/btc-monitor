"""Append validated provisional 4H context snapshots to durable JSONL history.

The record is *not* a verified directional prediction. Its historical label
remains provisional and may not be passed to the confirmed signal archive.
Single writer only; CI must serialize commits with concurrency.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

GRADES = {"strongly_bearish", "bearish", "slightly_bearish", "neutral",
          "slightly_bullish", "bullish", "strongly_bullish"}
SOURCE = "Bitget USDT-FUTURES BTCUSDT latest.json"


def _time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timezone required")
    return stamp.astimezone(timezone.utc)


def append_context(record, archive):
    if (record.get("status") != "provisional" or
            record.get("grade") not in GRADES or
            record.get("source") != SOURCE or
            record.get("confidence") != "low"):
        raise ValueError("only explicitly provisional Bitget context is accepted")
    candle_time = _time(record["observed_at"])
    deriv_time = _time(record["derivatives_observed_at"])
    if deriv_time < candle_time or (deriv_time - candle_time).total_seconds() > 4 * 3600:
        raise ValueError("invalid derivatives observation time")
    if record.get("cvd_status") != "unavailable":
        raise ValueError("unexpected CVD status")
    key = candle_time.isoformat()
    entry = {
        "id": "bitget_4h_price_trend_v0.1:" + key,
        "observed_at": key,
        "derivatives_observed_at": deriv_time.isoformat(),
        "grade": record["grade"],
        "confidence": "low",
        "quality": "provisional_price_only",
        "source": SOURCE,
        "model_version": "price_trend_4h_v0.1",
        "price_score": record.get("price_score"),
        "price_vs_20_prior_pct": record.get("price_vs_20_prior_pct"),
        "volume_ratio": record.get("volume_ratio"),
        "funding_rate": record.get("funding_rate"),
        "open_interest": record.get("open_interest"),
        "oi_change_pct": record.get("oi_change_pct"),
        "cvd_status": "unavailable",
        "hypothesis_a": "not_evaluated",
        "hypothesis_b": "not_evaluated",
    }
    path = Path(archive)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        existing = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for prior in existing:
        if prior["id"] == entry["id"]:
            if prior != entry:
                raise ValueError("conflicting observation for existing closed 4H candle")
            return False
    existing.append(entry)
    existing.sort(key=lambda x: x["observed_at"])
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                                 for row in existing), encoding="utf-8")
    temporary.replace(path)
    return True
