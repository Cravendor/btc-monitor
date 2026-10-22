# BTC 4H historical dashboard — safe Pages integration

Status: **development only**, not deployed.

## Release gates

1. GitHub Actions `BTC Historical Trend Dashboard Preview` completes successfully.
2. Inspect the generated HTML artifact and confirm it contains only archived real observations.
3. Populate `data/history/bitget_4h_context.jsonl` with multiple distinct closed 4H candles through a separately approved single-writer pipeline. A one-row preview does not establish 24h, 7d, or 30d trends.
4. Confirm a freshness check and no look-ahead bias. Existing `latest.json` is a snapshot, not a historical series.
5. Publish the generated static page to a separate `btc-history.html` path only after validation. Do not replace `index.html`.
6. Add a navigation link from the existing dashboard only after the page exists and works.
7. Keep provisional grades separate from validated prediction accuracy and the A/B macro hypotheses.

## Proposed read-only publication

A workflow can build the page from versioned historical JSONL and upload the HTML as an artifact. A future explicit deployment change can copy it to a separate Pages path, with the standard Pages permissions and branch policy reviewed first.

## Quality behavior

- No baseline at a window boundary: show `ONTBREEKT`.
- No current measurement or stale latest candle: show `ONTBREEKT`.
- Different model versions: never compare grades.
- CVD unavailable: do not assert absorption or distribution.
- Model grades are provisional 4H price-structure grades, not a macro-cycle forecast.
