# CVD interval validation (preparation, no paid services)

The current four-hour GitHub Actions job captures snapshots, **not** a continuous trade stream. It must not publish 4H CVD from a handful of recent trades.

This branch adds a fail-closed validator and tests. The collector's `cvd_4h` remains `not_collected` and `value: null` until a genuine full-interval source is implemented and verified.

Requirements for a future free collector:
1. Store **taker/aggressor** buy/sell trade records separately for spot and USDT perpetual futures, with venue, trade ID, UTC millisecond timestamp and BTC base quantity.
2. Collect continuously or backfill a documented complete historical trade source. Preserve pagination cursors/checkpoints, rate limits, reconnect gaps, and immutable archived chunks. GitHub's four-hourly job alone does not prove continuous coverage.
3. Validate each closed UTC 00/04/08/12/16/20 four-hour window: complete source range, pagination exhausted, no dropped reconnect periods, unique IDs, exact time boundaries, valid taker direction and consistent BTC units.
4. Only then call `validate_coverage(..., source_complete=True, gaps_checked=True, pagination_complete=True)`. These flags are evidence from the collector, **not** values to set unconditionally.
5. Publish per-venue `spot_cvd_4h` and `perp_cvd_4h` only for fully validated windows; include source URLs, coverage diagnostics, window bounds and UTC timestamps. A rolling CVD additionally requires an explicit baseline.
6. If any proof is missing, publish `status: incomplete` or `not_collected` and `value: null`, never zero. Preserve existing price/OI/funding/candle schema.
7. Confirm free hosting/API access and GitHub Actions usage before enabling any scheduled stream collector. No paid services, trials or new infrastructure are activated by this branch.

Run `python3 -m unittest discover -s tests` before merge.
