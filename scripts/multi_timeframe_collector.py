"""Fetch native Bitget BTCUSDT USDT-FUTURES candles for supported intervals.

Uses only public API endpoints. Each interval has independent status; failures
must not be interpreted as neutral or as zero. No weekly request until its
exchange calendar alignment is explicitly validated.
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
    output["1w"] = {
        "status": "not_collected", "data": None,
        "signal": {"status": "unavailable", "timeframe": "1w",
                   "reason": "weekly exchange candle boundary not yet validated"}}
    return output
