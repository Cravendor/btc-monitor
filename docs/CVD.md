# CVD-4H — public REST backfill, budget €0

`scripts/cvd.py` uses Bitget `/api/v2/mix/market/fills-history`, without
credentials, paid APIs or an always-on server. The existing BTC market snapshots
workflow calls it after collecting candles. No new service is activated.

## Interval and validation

- Latest closed UTC interval `[start, end)`, aligned to 00/04/08/12/16/20 UTC.
- Fixed query bounds, `endTime=end-1`, 1,000 trades per page, and strictly
  decreasing `idLessThan` cursor using the minimum returned trade ID.
- Pagination must terminate with an empty page, including after a short page.
  Non-contiguous trade IDs do not by themselves imply a missing trade.
- Validate symbol, timestamp, positive finite price/size and Buy/Sell direction.
  Deduplicate IDs, reject conflicting duplicates and stalled cursors.
- Reconcile summed base AND quote volume against the corresponding closed candle.
  Absolute rounding tolerances: 0.00000001 BTC and 0.01 USDT. No percentage
  tolerance that silently accepts missing volume. An empty interval is valid
  only if the candle confirms zero base and quote volume.
- Maximum 1,500 pages / 180 seconds; 0.12 seconds between requests. API failures,
  timeouts, limits and mismatches yield `missing_data`, `value: null`, `data: null`.
  No partial value or old result is silently substituted. A later run retries
  its latest closed interval; missed historical intervals are not fabricated.

`metrics.cvd_4h` and the compatible top-level `cvd_4h` contain the same result.
The dated snapshot is archived and included in `data/latest.json` through the
existing feed builder. Metadata includes interval boundaries, page count,
coverage, reconciliation errors and trade count. The dashboard renders the
metric and exposes its metadata; missing data displays Ontbreekt.

This is a per-interval signed trade delta, reset every 4H, not a continuous CVD
series. Buy volume minus sell volume, denominated in BTC, for Bitget USDT futures
only. It cannot establish spot accumulation or market-wide orderflow. Completion
is based on provider pagination and candle reconciliation, not independently
verified exchange sequence numbers; provider omissions can remain undetectable.
The public schema describes side as Buy/Sell, without a separate maker/taker flag.
Interpret it as the public trade direction; aggressor semantics should be
confirmed against an independently observed trade stream before trading use.

## Workflows and verification

Only `.github/workflows/` runs in GitHub; the copies under `workflows/` are inert.
`btc.yml` retains its four-hour schedule, tests, archived failures and explicit
incomplete-job failure. Its five-minute timeout accommodates the bounded backfill.
Pages fetches latest.json from the raw main-branch URL, so data commits do not
require a Pages rebuild. The Pages workflow also validates Python tests before
publishing dashboard changes.

Run `python3 -m unittest discover -s tests`. Fixtures cover paging, boundaries,
deduplication, stalled cursors, invalid trades, limits and volume mismatches.
A fixture pass does not prove that a real exchange interval reconciles. Check
the first scheduled run for `coverage: complete_reconciled` before treating CVD
as available. If it fails, inspect `reason`; do not loosen validation to force OK.

Source: https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
