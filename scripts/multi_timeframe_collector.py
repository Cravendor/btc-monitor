"""Fetch native Bitget BTCUSDT USDT-FUTURES candles for supported intervals.

Uses only public API endpoints. Each interval has independent status; failures
must not be interpreted as neutral or as zero. Weekly history is fetched in bounded 84-day windows and validated strictly.
"""
from datetime import datetime, timezone
from urllib.parse import urlencode

try:
    from .enrich import BASE, request
    from .native_timeframe_candles import GRANULARITIES, validate_rows
    from .multi_timeframe_signals import assess
except ImportError:
    from enrich import BASE, request
    from native_timeframe_candles import GRANULARITIES, validate_rows
    from multi_timeframe_signals import assess


def collect_native_timeframes(now=None, requester=request):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone required")
    timestamp = now.isoformat()
    output = {}
    for tf, granularity in GRANULARITIES.items():
        if tf == "1w":
            # Historical API windows are limited to 90 days. Fetch three
            # overlapping 84-day windows for at least 24 closed weeks.
            period = 604800000
            offset = 4 * 86400000
            current = int(now.timestamp() * 1000)
            boundary = (current - offset) // period * period + offset
            all_rows = []
            errors = []
            urls = []
            for i in range(3):
                end = boundary - i * 12 * period
                start = end - 12 * period
                url = BASE + "mix/market/history-candles?" + urlencode({
                    "symbol": "BTCUSDT", "productType": "USDT-FUTURES",
                    "granularity": "1Wutc", "startTime": start,
                    "endTime": end, "limit": 100})
                urls.append(url)
                part = requester(url, lambda rows: rows, True)
                if part.get("status") != "ok" or not isinstance(part.get("data"), list):
                    errors.append(part.get("error", "invalid weekly history response"))
                    break
                all_rows.extend(part["data"])
            if errors:
                output[tf] = {"status": "error", "data": None,
                              "error": "; ".join(errors)[:200], "urls": urls,
                              "signal": {"status": "unavailable", "timeframe": tf,
                                         "reason": "weekly history fetch failed"}}
            else:
                try:
                    validated = validate_rows(all_rows, tf, timestamp)
                    signal = assess(validated["candles"], tf, timestamp)
                    output[tf] = {"status": "ok" if signal["status"] == "provisional" else "missing_data",
                                  "data": validated, "signal": signal, "urls": urls,
                                  "observed_at": timestamp}
                except ValueError as exc:
                    output[tf] = {"status": "error", "data": None,
                                  "error": str(exc)[:200], "urls": urls,
                                  "signal": {"status": "unavailable", "timeframe": tf,
                                             "reason": "weekly candle validation failed"}}
            continue
        url = BASE + "mix/market/candles?" + urlencode({
            "symbol": "BTCUSDT", "productType": "USDT-FUTURES",
            "granularity": granularity, "limit": 100})
        def transform(rows, interval=tf):
            return validate_rows(rows, interval, timestamp)
        metric = requester(url, transform, True)
        if metric.get("status") == "ok":
            result = assess(metric["data"]["candles"], tf, timestamp)
            metric["signal"] = result
            if result.get("status") != "provisional":
                metric["status"] = "missing_data"
                metric["error"] = result.get("reason", "signal unavailable")
        else:
            metric["signal"] = {"status": "unavailable", "timeframe": tf,
                                "reason": "native candle source unavailable"}
        output[tf] = metric
    return output
