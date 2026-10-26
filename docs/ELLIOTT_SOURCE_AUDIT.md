# Weekly source discrepancy — 26 October 2026

## Scope and original evidence

Bitget BTCUSDT USDT-FUTURES trade-price candles, UTC window October 19 00:00
through October 26 00:00. Three new public API requests at 18:21–18:22
Europe/Amsterdam reproduce the stored discrepancy. Original response rows,
query URLs, observation times and row checksums are preserved in
[data/history/source-audits/20261026T172221Z-week-day-4h.json](../data/history/source-audits/20261026T172221Z-week-day-4h.json).
No credentials, private NAS logs or database content are included.

| Measurement | Native 1Wutc | Seven 1Dutc candles | 42 native 4H candles |
| --- | ---: | ---: | ---: |
| Open USDT | 82066 | 82066 | 82066 |
| High USDT | 84870 | 84870 | 84870 |
| Low USDT | 79170.3 | 79170.3 | 79170.3 |
| Close USDT | 80125.5 | 80119.2 | 80119.2 |
| Base volume BTC | 217958.4979 | 217958.5411 | 217958.5411 |
| Quote volume USDT | 17880279058.44215 | 17880282519.78240 | 17880282519.78240 |

Weekly minus aggregated daily: close +6.3 USDT, base volume -0.0432 BTC,
quote volume -3461.34025 USDT. The original string values also disagree, so
this particular conflict is not introduced by float normalization. All seven
fresh daily groups match their fresh native 4H children in OHLC/base volume.
These are related feeds from one provider, not three independent market votes.

Official API definition:
https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
(Get Historical Candlestick) explicitly identifies 1Wutc / 1Dutc as UTC lines,
the close as a finished-candle value, base volume in field 5 and quote in field 6.
The archived queries use that trade-price endpoint and aligned closed boundaries;
no spot/mark/index series is substituted.

## What is established and what remains unknown

The conflict remains reproducible directly in the current API responses and is
not a stale local file. This does not prove which native value is correct or why
Bitget's endpoints differ. Do not silently replace the native week with a derived
week, loosen the equality rule, infer a confirmed wave, or rewrite original
candles. The weekly chart remains blocked. Future corrected source data require
an explicit version preserving review/reconciliation before activation.

The proposed diagnostic change includes up to five exact per-candle/per-field
mismatches in reconciliation output, shows the first mismatch in the dashboard,
and prints the final source review in collector logs. It does not change the
acceptance gate. This addresses the misleading complete-fetch log followed by
exit 1: history workflow 40367287095 fetched/committed its new native rows and
then correctly failed the source review, not its Git push. At its 17:18 UTC
checkpoint, 4H/hour coverage was complete (2896 and 11585), superseding the
earlier temporary missing 12:00 4H candle. Later closed windows still need checks.

## Separate stale snapshot finding

The latest published observation at 15:13:12 UTC / 16:13:12 Amsterdam is labeled
github_fallback and contains no collected CVD. Last published NAS observation
remains 08:34:11 UTC / 09:34:11 Amsterdam. The reserve is not a replacement for
NAS CVD collection. Public history cannot establish current DSM process/task
state or why the NAS stopped publishing.

Collector-health run 40367246156 was triggered by a push. Its event_not_eligible
result is intentional: only schedule/manual health checks may attempt reserve
collection. It published the stale result before exiting 1. Recent public cron
runs observed at 07:48 and 15:12 UTC do not demonstrate the configured twice-
hourly cadence actually executing. Do not assume an exact future run time.

Next evidence: user supplies the latest already-finished first-upload.txt from
the existing BTC NAS Collect Publish task, including EINDSTATUS if present.
No extra manual execution, duplicate task, restart or old recovery command is
requested. Inspect the log before proposing a NAS repair. True linked Elliott
wave-degree development can proceed independently of that private evidence.
