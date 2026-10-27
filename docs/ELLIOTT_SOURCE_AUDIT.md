# Weekly source discrepancy — 26 October 2026

## Follow-up: source revisions now reconcile — 27 October 2026

This section supersedes the statement below that the weekly discrepancy still
reproduces in current API responses. The October 26 observation remains a valid
historical observation; no earlier audit has been edited or deleted.

Fresh public native trade-price requests at 05:24:13–05:24:26 UTC / 06:24–06:24 CET,
followed by exact replays of the three original query URLs at05:26:40–05:26:49 UTC,
now agree. Both query windows return the same replacement row in each case.
Original response values, request URLs/times and original cached rows/archive
hashes are in [the follow-up audit](../data/history/source-audits/20261027T052431Z-week-day-4h-1h.json).
These remain related provider feeds, not independent market votes.

| Native candle | Previous cached value | Fresh native value |
| --- | ---: | ---: |
| Week October19 close USDT | 80125.5 | 80119.2 |
| Week October19 base volume BTC | 217958.4979 | 217958.5411 |
| Day October26 high USDT | 80200 | 80812.6 |
| Day October26 low USDT | 79969.3 | 79320.1 |
| Day October26 close USDT | 80100.1 | 80117.1 |
| Day October26 base volume BTC | 483.6814 | 34528.9542 |
| 4H October26 20UTC close USDT | 80120.3 | 80117.1 |
| 4H October26 20UTC base volume BTC | 2502.5057 | 2636.9999 |

The audit includes exact quote-volume changes too. Fresh raw-string Decimal
comparison checks all six OHLC/base/quote fields:48 complete4H groups agree with
1H children,8 daily groups agree with4H,1 closed weekly group agrees with daily.
All193 fetched1H rows, including the preceding boundary row, agree with cached
1H rows. The changed native weekly row was originally observed October26 01:46
UTC; the daily/4H rows October27 00:06UTC. We observe source revision; Bitget's
internal reason/timing or whether a cache/finalization delay caused it is NOT
established. No timezone, tolerance or mark/index/spot substitution was applied.

## Reviewed cache correction and remaining limits

Proposed branch replaces exactly these three current-cache rows with the native
replayed values, preserves their full previous rows and original page metadata
in the audit, and appends provenance entries linking the revision audit and prior
archive hashes. Original NAS observations/reports and the older source audit are
unchanged. This is an explicit source revision, not a claim that earlier analytics
had these corrected values available at their original observation times.

After correction, the existing bounded history collector resumes successfully:
one new4H candle and five new1H candles are added (October27 00–04UTC). Strict
loader/hash and whole-history reconciliation now pass:69 weekly,483 daily,
2899 four-hour and11597 hourly candles through the current boundaries at05:30UTC.
Latest closed bounds:week Oct26 00UTC,day Oct27 00UTC,4H Oct27 04UTC,1H Oct27 05UTC.
The source gate will still block any future discrepancy. This is a reviewed
one-off correction, not an implemented automatic source-revision policy.

Preview has all four timeframes available and42 source-derived SVG charts.
That does not certify a wave or create probabilities. Weekly/day/4H each have
only an unresolved one-pivot-leg prefix; other proposals are invalid; all four
hourly proposals invalid at this cut-off. Counts are tentative, no preferred ID.

Validation:490 Python tests,6 Node tests, strict original-row retention check,
complete offline staging/actual SVG content-count gate and whitespace passed.
The release CI path filter now includes data/history/** so a historical-input PR
also exercises both Python versions and the actual dashboard gate. Public
acceptance of this correction awaits reviewed merge and successful Pages.
No NAS task, recorder, database, credentials or paid API was changed or invoked.

The existing collector stops on overlapping source revisions to preserve data;
it does not automatically refresh already-complete cached rows. Next development
can implement a bounded revision audit/activation policy preserving originals
and as-observed history. This can begin independently of the public acceptance.
No extra manual NAS action is required.

## Original audit — 26 October 2026

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
