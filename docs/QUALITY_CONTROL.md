# Quality control before reports and dashboard publication

Checkpoint: 25 October 2026. User requested a quality gate on every scheduled
report/alert and frequent dashboard checks, with active recovery after rejection.
Budget remains EUR 0. No additional scheduled task is introduced.

## Actual execution, not a separate fictitious reviewer

All five currently enabled financial tasks received a mandatory pre-publication
quality/recovery step on 25 October. The monthly Quality & Improvement task had
no recorded execution and begins 1 November. It is a deeper review, NOT the
per-report gate. The new gate runs inside each existing task; a prompt update
is not proof of a future execution or an independently run second reviewer.
Existing schedules, market-alert conditions and silence rules are preserved.

Before output, each task must read actual source content, validate identity,
source/observation times, units and calculations, compare like closed windows,
and verify that conclusions follow from the evidence. Re-fetch failed public
sources and recalculate before accepting a result. Read GitHub blobs by returned
SHA when large contents responses are empty. Use available valid components for
an explicitly limited report. Missing macro evidence means NOT ASSESSABLE, not
neutral. Repeated absence requires diagnosis, a concrete action and follow-up;
never merely repeat ONTBREEKT or claim no risk from inaccessible data.

Safe code repairs may be prepared/tested in a separate PR under the latest user
authorization. Do not automatically merge, force-push, restart NAS processes,
change the journal, activate paid services or silently change model thresholds.
Where access is missing, disclose the specific remaining blocker. The normal
market-alert rules still determine whether a notification is appropriate.

## Executable dashboard checks

- Each new collected snapshot gets `analysis_quality`: source identity/freshness,
  actual finite price, closed contiguous 4H candles, per-metric failures,
  recomputation of native timeframe signals, per-market CVD proof, and comparison
  of frozen scenario outputs with recomputation from original snapshot inputs.
- The existing half-hour health workflow repeats this review, distinguishes
  repeated snapshots from distinct failed 4H intervals, and audits latest
  original reports for detectable contradictions. A current but invalid primary
  price/candle source can invoke the existing bounded public reserve. CVD-only
  failures do not invoke a cloud collector that cannot access the NAS journal.
- The existing NAS pipeline retries incomplete historical recovery at subsequent
  uploads. Volume mismatches get one alternate documented candle request for
  the SAME closed candle, within the same request/time budget; exact equality
  and journal replay requirements remain unchanged. No unlimited retry loop.
- Before Pages uploads its artifact, the new gate recomputes quality and checks
  required dashboard assets and the quality panel. It writes btc-quality.json.
  Broken required assets fail publication. Limited source data publish an
  explicit degraded panel instead of leaving an old green page live.
- Home and task-status pages show scope-specific data quality. Browser expiry
  prevents the home panel's valid scope surviving a new 4H window unchallenged.
- New archive submissions with the explicit contradiction "macro neutral because
  insufficient data" are rejected. Existing originals remain immutable and are
  flagged for review. This narrow linter does NOT verify every prose claim;
  source/claim checking remains part of the mandatory task execution.

This is event/update-based plus existing periodic checking, not a continuously
running autonomous human-equivalent reviewer. It does not establish forecast
accuracy, complete on-chain/macro coverage, independent aggressor attribution,
or a valid cycle-bottom verdict merely because transport/tests are green.

## Follow-up

Merge/publication, NAS code uptake, fresh original snapshot quality fields,
first measured recovery diagnostics and actual scheduled-task compliance must
be verified separately. Read docs/CVD_RECONCILIATION.md for this incident's
measured evidence and remaining uncertainty. Do not claim those post-merge
acceptance steps were completed by local tests.
