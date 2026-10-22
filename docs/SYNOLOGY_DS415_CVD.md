# DS415+ — zero-subscription CVD preparation

**State: storage/journal and tests only. NOT a working Bitget stream collector.**
The DS415+ is an older x86 Synology. Python 3 availability, DSM version,
TLS certificates and WebSocket library compatibility must be checked on the
actual NAS before choosing a runtime. Do not assume Docker/Container Manager
is available on this model.

## Safe deployment approach

1. On the DS415+, inspect DSM version, Python 3 availability and free disk
   space in Package Center/Control Panel. Do not expose SSH to the internet.
2. Make a shared folder such as `btc-cvd` on an existing volume. Keep the
   SQLite database there so restarts do not erase trades.
3. This branch currently provides `scripts/cvd_store.py`, which uses only
   the Python standard library for SQLite storage and atomic health export.
   A supported WebSocket client/runtime has **not** been installed.
4. Future collection requires two distinct Bitget public trade feeds:
   BTCUSDT spot and BTCUSDT USDT perpetuals. Verify official endpoint,
   symbol, channel, trade ID and **aggressor side semantics** against current
   documentation before implementation.
5. On every connection loss, restart or data gap, write a gap record. A
   reconnect does not magically restore missed trades. Backfill must prove
   full coverage or the interval remains incomplete.
6. Never report journal counts or summed trades as complete 4H CVD. The
   existing `data/latest.json` CVD field remains `not_collected` until
   coverage validation and safe GitHub ingestion are implemented.
7. Do not store GitHub tokens in the public repository. If later using
   uploads, use a scoped credential stored in DSM's protected task settings
   and rotate/revoke it if leaked. Prefer pull-based ingestion where possible.

## Readiness checks

- Python version and available websocket packages confirmed on NAS
- Stable 24/7 connectivity and enough persistent disk space
- Reconnect, backfill, UTC alignment and trade-ID dedup tested
- Independent completeness checks available (not just booleans asserted)
- Export integrated and validated with `data/latest.json` and dashboard
- No paid APIs or cloud hosting required

The NAS may already be powered on, but electricity, bandwidth and disk wear
still have real costs. This preparation does not change the running monitor.
