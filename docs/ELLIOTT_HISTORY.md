# Long Elliott candle history — 25 October 2026

Requested range: 1 July 2025 through the latest closed candle, covering the final
two quarters of 2025 and elapsed 2026. Weekly UTC candles include the week that
starts 30 June 2025. Scope: Bitget BTCUSDT USDT-FUTURES, native trade-price OHLCV.

The existing validated daily archive already covers this period. Reuse it
without rewriting its originals. Add separate native weekly, 4H and 1H archives
under data/history/elliott. This corrects the visual adapter's prior use of only
36 weeks and 89 daily snapshot candles despite the longer daily archive existing.

## Collection and recovery

Use the public /api/v2/mix/market/history-candles endpoint. A page contains at
most 192 target intraday candles plus a preceding overlap; weekly pages use 11
target weeks plus one overlap, within 90 days. Each full validated response is
atomically checkpointed with query URL, observed time and content checksum.
Resume the earliest missing interval in round-robin order. Identity, alignment,
closed status, OHLC geometry, volume, duplicates and cache integrity are checked.
Incomplete responses and source revisions stop the affected degree without
replacing its accepted candles or fabricating a gap. Runs have explicit page
and wall-clock limits; completed pages survive the next session.

The existing daily-history workflow also runs the bounded Elliott collector.
Its daily cron remains unchanged. Trusted completions of the existing market
snapshot/health workflows trigger another bounded session and update new closed
candles. No additional scheduled task is created. A rejected ordinary Git push
still requires follow-up; this is not a general concurrent-writer repair.

## Initial source evidence

Actual collection completed in multiple bounded local sessions. Independent
coverage review at 2026-10-25 13:58:05 UTC found:

| Timeframe | Candles | Missing | Closed through UTC |
| --- | ---: | ---: | --- |
| Week | 68 | 0 | 2026-10-19 00:00 |
| Day | 481 | 0 | 2026-10-25 00:00 |
| 4H | 2,889 | 0 | 2026-10-25 12:00 |
| 1H | 11,557 | 0 | 2026-10-25 13:00 |

Prices and BTC base volume reconcile exactly in all 2,889 hour-to-4H groups,
481 4H-to-day groups and 68 day-to-week groups. The first weekly check uses the
existing daily archive's 30 June candle as well. No groups were skipped.
Maximum USDT quote-volume differences in normalized values were respectively
0.0000013, 0.0000017 and 0.000010. These are diagnostic observations, not proof
of raw provider precision or justification for relaxing exact CVD validation.
Price/base-volume conflicts reject the affected parent chart. Coverage and
cross-timeframe results are exposed in coverage.json and the dashboard quality
artifact. They are recomputed; a saved complete label is not trusted forever.

## Chart behavior and limits

Week/day show the whole selected source period with the period high and later
running low as structural references. Lower charts zoom to at least 400 recent
candles plus their candidate window while candidate selection reads all stored
candles. An available 1H closing price is explicitly labeled on higher charts;
it is neither a live tick nor a closed higher-timeframe candle.

Checked historical prefixes remain visible with the exact missing interval and
an incomplete warning; no line bridges a gap and no shorter snapshot silently
replaces the requested long archive. Missing/invalid archives stay unavailable.
The previous latest-six-pivot candidate method remains explicit and provisional.
More history does not itself prove a current wave, a complete bear impulse or
nested 5-3-5-3-5. Original reports/scores and route-anchor policy remain separate.

Validation: 429 Python tests and five Node status tests pass locally; full
read-only dashboard generation/quality staging and weekly SVG rendering were
checked. CI, merge, public data availability and workflow-driven incremental
refresh require separate verification after publication.

Primary API method reference:
https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
(section Get Historical Candlestick).

## Post-merge publication checkpoint

PR #75 is merged. The first actual history workflow successfully added the next
closed hour (11,558 total). Live quality at 2026-10-25 14:20:29 UTC reports all
four source degrees complete, zero gaps and eight rendered charts. This is
evidence for that run/window, not guaranteed future scheduling.

Follow-up: Pages must also watch completion of `BTC multi-year daily history`.
History commits use the built-in Actions token; their pushes do not themselves
start other workflows. The first update happened to be included by another
pending Pages run. An explicit completion trigger removes this timing dependency,
reusing the existing trusted-default-branch guards and degraded-publication rules.
No schedule, source data or collection code is changed by this follow-up.

## Reproduced weekly conflict — 26 October 2026

See [ELLIOTT_SOURCE_AUDIT.md](ELLIOTT_SOURCE_AUDIT.md) for preserved fresh API
responses and exact field differences. Full row coverage does not establish
cross-timeframe consistency. The weekly acceptance gate remains unchanged.
