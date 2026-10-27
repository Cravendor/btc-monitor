# Bounded closed-candle revision audit

`scripts.source_revision_audit` rechecks the last TWO cached closed candles of
each native Bitget BTCUSDT USDT-FUTURES scale:1Wutc,1Dutc,4H,1H. It records
cached/current values and validated original seven-field response rows without
changing active candle files, snapshots, reports, thresholds or wave counts.
This is revision detection/evidence, not automatic approval or activation.

The existing history workflow runs it after both history collectors, including
when their captured exit status is nonzero. A changed complete cache can therefore
be investigated even though the gap-filling collectors skip already-complete
ranges. No additional schedule, credential or paid service is introduced.

## Bounds and interpretation

- Validate cache market/schema/checksum and a contiguous two-candle tail first.
- At most four credential-free requests, one per scale;75-second overall budget,
  15-second request allowance, at most three returned closed rows including the
  preceding boundary row. The query limit is10; unexpected windows are rejected.
- Select the two latest cached candles, not imaginary missing newer candles.
  `start`, `end`, `required_through` and `cache_tail_current` distinguish that
  limited window from full current coverage. An unchanged historical tail does
  not certify current or complete history.
- Use exact equality for the six NORMALIZED cached OHLC/base/quote fields. The
  original source row strings are retained too. Do not mistake binary-normalized
  cache comparison for independent verification of all original raw precision.
- `as_of` fixes selection boundaries;per-check `observed_at` comes from the shared
  request helper and denotes its request-start time. This is not a frozen forecast
  ledger or an exact finished-response availability timestamp for calibration.
- Source revision, unavailable/invalid response, stale/future observation and
  budget omission stay distinct from an unchanged tested window. Source failures
  are sanitized to fixed reason labels;arbitrary requester metadata is discarded.
- Only two cached candles per scale are rechecked. Older revisions, other markets,
  and cross-timeframe agreement are outside this audit. Existing whole-history
  source reconciliation remains separate and unchanged. Provider-internal causes
  or truth cannot be established from a detected normalized difference alone.

Statuses:`unchanged_checked_windows` only when all four tested windows agree;
`revision_detected` if any changed, retaining unavailable states of other scales;
otherwise `incomplete_audit`. The CLI exits1 on revision or incomplete audit,
otherwise0. This drives the history workflow result; it is not a new chart-source
activation/gating policy or an automated resolution of detected revisions.

## Evidence persistence

Each run writes a unique JSON under `data/history/source-revision-audits/`, named
with UTC selection timestamp and full SHA256 of canonical audit content. Stage a
complete file outside that published directory, then atomically create a hard
link with no overwrite. Identical replay is idempotent;an existing different file
at the same name is an error, never replaced. Original input caches stay intact.

The CLI also writes the single current public audit to
`output/source-revision-audit.json`. The workflow commits the immutable audit
directory after history changes, then returns the captured audit/history status.
An `always()` artifact step retains ONLY the current audit for30 days, including
when a Git push fails. It does not upload all accumulated historical audits or
promise a failed Git push nevertheless reached main. Artifact preservation is
configured and locally generated;its first real workflow acceptance is pending.

Public API reference:
https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
(Get Historical Candlestick;native UTC scales and finished-candle field semantics).
No mark/index/spot replacement or relaxed equality rule is used.

## Observed validation and remaining acceptance

Live local probe at2026-10-27T07:56:15UTC /08:56:15CET:all four selected windows
unchanged against the PR88 corrected cache. Week/day/4H tail current at that
cut-off;1H tail historical through05UTC versus required07UTC. The probe correctly
does NOT call the hourly history current. Original public evidence is committed
alongside this change. It does not claim this proposed auditor already ran on a
scheduled GitHub workflow or that PR88's correction is deployed.

Local validation:501 Python tests,6 Node tests, YAML parsing, whitespace and full
offline dashboard/source-SVG gate passed (42 charts at its recorded input). Eleven
new tests cover all four bounded requests, cache immutability, quote-only changes,
malformed/missing/future/unavailable data, historical tails, cache tampering and
read races, raw/normalized mismatch, budget omission, immutable evidence,
idempotence/collision and failed atomic publication without partial files.

Next:reviewed PR88 merge, successful Pages and actual source-chart acceptance;
then observe the first existing history workflow's audit JSON/artifact/result.
No extra manual collection or operational task is required. Exact higher-anchor
linkage for forming prefixes can be developed independently. Automatic revision
activation still needs a reviewed policy preserving original and revised views;
probabilities still need frozen outcomes and out-of-time calibration.
