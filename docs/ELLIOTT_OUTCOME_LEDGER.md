# Experimental frozen Elliott observations

This is an opt-in library foundation, not a historical backtest. A separately
proposed workflow capture is described in ELLIOTT_OBSERVATION_RUNNER.md. `freeze` records the exact closed normalized candles and complete
forming-inventory output as supplied at an observation time, with content hash.
`evaluate` rebuilds that original inventory and checks the same fixed candidate
anchors against each subsequent closed candle in order, retaining the first
observed hard-rule violation. Original invalid candidates remain separately
marked. An unresolved result does not mean the scenario succeeded, that a wave
finished or that price will move in a particular direction. No probabilities,
profit targets or trading signals are calculated.

Both operations require a caller-provided `complete` source state, current closed
coverage, valid contiguous candles and unchanged original inputs. The evaluator
rejects original source revisions, missing data and modified inventory. It does
not infer intrabar ordering and records only the candle closing time at which a
violation became known. The immutable helper uses a content-addressed file with
atomic create-only linking, rejects tampering and leaves originals intact.

The caller's source-state argument and observation time are NOT independently
verified by this library. It must not be used to manufacture historical forecasts.
A separately reviewed production integration must derive source eligibility from
validated native sources and cross-timeframe reconciliation, record actual
observation times and immutable original source versions, define durable storage,
retention, concurrent-writer behavior and a correction/revision policy, and
connect to the existing workflow without duplicate schedules. Source conflicts
must remain unavailable. Storage cost of full candle arrays per observation must
be addressed before frequent automated capture. Evaluation is not wired to a
workflow or dashboard, and no live records are written by this change.

Future work includes outcome definitions beyond rule invalidation, bounded
availability and missing-evidence records, non-overlapping evaluation, source
revision-aware as-observed histories and statistically defensible out-of-time
calibration. No accuracy or predictive usefulness follows from this foundation.

## Seven-day workflow proposal

See [ELLIOTT_SEVEN_DAY_OUTCOMES.md](ELLIOTT_SEVEN_DAY_OUTCOMES.md). The new
evaluation model explicitly marks a violation in the first partially observed
candle as ambiguous, and reports candle-close time separately from actual
processing time. Existing fixed-anchor snapshot model remains unchanged.
