# Multi-year Bitget daily history

The public, same-instrument archive starts at 2021-01-01 UTC. This is a collection
target, not an inferred previous cycle peak. It is stored separately from normal
NAS snapshots at `data/history/bitget_btcusdt_daily.json`.

The documented endpoint is:
https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
(section Get Historical Candlestick, `/api/v2/mix/market/history-candles`).
Use BTCUSDT, USDT-FUTURES and 1Dutc. Each request covers 84 target days plus a
one-day overlap, within the documented 90-day range and 200-row limit. Validate
UTC alignment, positive finite OHLC, candle geometry and nonnegative volumes.
Only closed days count. A returned open upper-bound day is excluded. Returned
days must match the requested window; missing days, empty windows, source errors
and conflicting revisions never become zero-valued or fabricated candles.

Each complete page is atomically checkpointed with request URL, observation time,
interval and source provenance. A SHA-256 covers normalized candle content.
Cached identity, duplicate-day and checksum validation precede every resume.
A run has a 32-page/150-second default budget and requests only missing intervals.
A partial run exits nonzero but leaves valid completed pages available for resume.
The API request itself has the existing 15-second timeout and no paid fallback.
An empty response is insufficient data, not proof of an instrument launch date.

`BTC multi-year daily history` runs on public GitHub runners: initial code push,
manual dispatch or daily at 04:17 UTC. It shares the existing GitHub-writer
concurrency group, stages only the dedicated history file and uses an ordinary
push. It does not serialize the NAS itself. A concurrent upstream push may reject
publication; no force-push, generated-feed overwrite or destructive recovery is
attempted. Only successfully pushed checkpoints are durable beyond that runner.
The next executed run resumes from the committed source file.

The NAS publication runner does not download years of data. Normal collection
only reads and validates the local archive after the existing Git update, and
records `cycle_history_reference` metadata alongside its original snapshot.
Cache absence/corruption is separately unavailable and does not block ordinary
market publication or alter its global status. Coverage is independently
recomputed through the latest closed UTC day; a new missing day makes it partial,
even if a stored status previously said complete. The dashboard displays this
metadata with its snapshot timestamp, without claiming it is a live data refresh.

History is not automatically a cycle classification. The prepared cycle-anchor
policy remains opt-in; no prior peak/phase is inferred or activated here. A future
adapter still needs an explicit prior cycle peak, phase rationale, full relevant
coverage and a fresh source context before activating those macroanchors. Current
observed-history routes are unchanged.

The subsequent [cycle-context adapter](CYCLE_CONTEXT.md) implements that read-only
connection with explicit draft/active configuration and archived review evidence.
Its shipped draft does not replace the current route anchors.

Validation: 361 unit tests pass, including exact range coverage, page-budget
resume, no duplicate downloads when complete, malformed/gapped/error responses,
revision conflicts, cache tampering, open-day exclusion and next-day missingness.
The existing source tests and read-only dashboard generation also remain covered.
