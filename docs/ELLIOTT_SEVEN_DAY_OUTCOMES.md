# Fixed-anchor seven-day outcome records

This proposed addition evaluates eligible, previously captured Elliott scenario
manifests in the existing history workflow. Its initial research window ends seven
days after the first native candle boundary at or after the original observation.
This is a fixed comparison window, not a forecast that price will move in seven
days. Weekly timeframes use Monday UTC boundaries; the window therefore starts
at the next weekly boundary when observation occurs midweek. No backfilled
scenario is created. No profit target, success rate or probability is inferred.

An original available manifest must be committed, pass its identity and content
hash, and reconstruct against its exact original Git sources, bounded audit and
model code. Before each run the later native source files must exactly match the
checked-out commit, be complete and cross-timeframe reconciled, and have a recent
matching bounded revision audit. Existing source conflicts block evaluation.
Any change to the original normalized candle prefix rejects evaluation rather than
silently rewriting it. A bounded audit checks recent candles, not all historical
revisions; later-period candle values are the version actually observed at the
recorded evaluation time, not proven to have been available at the horizon end.

The seven-day horizon is fixed in advance. Later candles are excluded even when
processing is delayed. The immutable outcome references the original manifest,
later source commit and hashes, current audit hash, actual processing time and
horizon. For each original candidate it records already-invalid, unresolved,
first subsequent rule invalidation, or ambiguous-first-candle status. The candle
close time is not represented as the time the data was actually seen; the actual
processing time is stored separately. The model remains unproven and probability
is null. Outcome model version is `elliott_invalidation_evaluation_v2`.

If a scenario was observed during an open candle, its high or low can predate the
observation. When that first candle contains a rule violation, its order cannot
be determined from OHLC: the result is `ambiguous_first_candle`, not a later
invalidation. No subsequent outcome is invented for that fixed candidate.

At most four due manifests are attempted per execution in chronological order.
Processing errors are explicit and make the workflow fail; repeated errors in the
oldest batch can delay later work until investigated. Ineligible inputs produce
no outcome and are recorded in the workflow status artifact. New records are
create-only and content-hashed. Normal workflow commit/push provides durability;
current records and the run status are also placed in a 30-day artifact if a push
fails, but real rejected-push recovery has not been tested. Full Git history is
fetched because observation sources reference older commits; this increases
checkout time and storage as history grows. History retention is required.

No actual eligible seven-day observation exists yet. Synthetic fixture tests are
not a live outcome acceptance. After deployment the existing workflow must first
capture a source-valid scenario, then its full seven-day horizon must elapse and
its later source inputs must pass the same guards before an outcome can appear.
