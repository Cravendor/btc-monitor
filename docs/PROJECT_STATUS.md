# BTC Monitor — current scope and open work

Checkpoint: 25 October 2026, Europe/Amsterdam. Reconciled through 48191e8 and
merged #76. Read [HANDOVER.md](HANDOVER.md) for the evidence ledger and NAS task
inventory, and [DECISIONS.md](DECISIONS.md) for accepted constraints.
This replaces the older accumulated preparation checkpoints in this file.

| Component | Verified checkpoint | Open boundary |
| --- | --- | --- |
| Public meters/routes | #60–#62 implemented; two routes/five directional states, versioned source observations | No calibrated probabilities or personal position state |
| Macroarchive/context | #63 / #65 merged; original automatic draft review observed | Config still draft; reference/phase activation requires separate review |
| Operational task page | #68 / #69 merged; execution receipts and individual cards exist | Missing/expired evidence is unavailable/stale, not stopped/running proof |
| Watchdog/storage | #70 / #72 merged; watchdog replacement reported | Current real receipts and storage installation need verification |
| NAS upload recovery | #71 merged and actual repair c4e2e94 confirmed; subsequent ordinary uploads succeeded | General concurrent-writer races not solved |
| CVD reconciliation | Original 08:32 UTC NAS record verifies both markets for 04–08 UTC, exact BTC/quote volumes | Original earlier mismatch cause unresolved; interval-by-interval proof required |
| Quality/recovery gates | #73 merged; per-snapshot and periodic/dashboard checks implemented | New NAS fields and actual scheduled report compliance need inspection |
| Elliott visuals | #74 merged; weekly/daily/4H/1H bull/bear candidates and eight charts | Provisional counts, nesting and psychological phase not proved |
| Long Elliott sources | #75 merged; July 2025 onward, 68 weeks / 481 days / 2,889 4H / 11,558 1H, zero gaps at 14:25 UTC | Coverage must be recomputed as new candles close |
| History completion to Pages | #76 merged; explicit trusted completion trigger present; post-merge Pages successful | Observed history 40218583040 → successful workflow_run Pages 40218606715; source association inferred from timing/head/configuration |
| Original reports/history | Immutable archives and execution receipts have actual commits | Not proof that every planned report ran/delivered |
| Macro/news and psychology | Contextual reports and candidate rules exist | No validated independent numerical macro/news vote or certified phase |
| Forward evaluation | General technical/scenario tooling exists | Dedicated two-route/25-combination analysis and sufficient 7/30/90-day follow-up |
| Visual QA | Prior desktop interaction, SVG checks and live quality checkpoint recorded | New full browser/mobile interaction QA remains open |

### Recovery of 4795253 confirmed — 25 October 2026

Actual supplied recovery result confirms verified external recovery-4795253.bundle
and successful push. Remote merge 7f4e17d8219a5d1f51fa3cf3d3ac2ab7d645d9ce
has parents 479525341c9d064f0930b6a533b339e00a001336 and 58c71a554debcfa1b1efbcbfe4dc622432938b0c.
The original data/2026/10/25/20261025T090120972251Z-local-1.json blob is identical
before/after recovery (767b3a6aeeda00ce3c22cccfeeaef111bb82d141).
Parsed local/upstream/merged timeframe histories have 110/112/113 rows;
every original row from BOTH inputs survives with identical content.
Pages run 40223527403 at recovery head completed successfully.
No raw private log was published.

This supersedes earlier “recovery ready/not executed” status for this incident.
It proves preservation/publication of the pending historical observation, not
a new NAS collection, current CVD coverage or recorder availability.
Next: manually execute the existing BTC NAS Collect Publish task once and inspect
its complete fresh result. Then verify new immutable NAS original, #73 quality/
recovery diagnostics, watchdog/storage receipts and associated Pages run.
Keep BTC Git Diagnose disabled for scheduling and do not rerun incident recovery.
Permanent NAS/GitHub concurrent-writer resilience remains open.

Validation: actual recovery result, remote merge parentage, original blob equality,
full original history-row union and successful Pages result. Documentation-only
checkpoint; no new runtime tests, DSM execution or new receipts claimed.

### Guarded recovery ready for local 4795253 — 25 October 2026

Read-only diagnosis confirms clean main, exactly one local commit and 36 upstream
commits: HEAD 479525341c9d064f0930b6a533b339e00a001336; fetched origin/main
9c165721cefa9b7714e8c17231d121bdc60ac6fa. Its changed-file set is exactly the
three generated views, timeframe signal history and added immutable original
data/2026/10/25/20261025T090120972251Z-local-1.json.
This matches the existing recover_pending_snapshot.py guarded contract.
No repair has been executed or published by this preparation.

Prepare the manual invocation through the existing disabled-for-scheduling
BTC Git Diagnose task: preserve the documented Git/SSH runtime, extract the
reviewed helper from fetched 9c165721 under the publisher lock to an external
helper path, then let it reacquire that same lock. Pass the full expected HEAD,
exact archive and NEW external recovery-4795253.bundle. The helper must refuse
changed/dirty state, active Git operations, unexpected paths, multiple pending
commits or conflicting original history. It verifies a backup before merging,
retains the dated original blob, unions histories and keeps upstream generated
views; no reset/clean/force-push or live recorder/database changes.
On failed push retain merge and backup and obtain a fresh diagnosis.

Next required result: inspect repair-result-4795253.txt for backup verification
and successful ordinary push. Only then run the existing BTC NAS Collect Publish
task and verify a fresh NAS original, current interval delta/quality fields,
receipts and Pages publication. Recurrent writer resilience remains open.
Validation: supplied diagnosis and unchanged helper guards reviewed; no new
runtime tests, NAS execution, repair, receipt or deployment claimed.

### Confirmed pending-upload conflict — 25 October 2026, 19:05 Amsterdam

The supplied latest upload result confirms failure at 18:05:28–18:05:32 UTC:
exit 1 while rebasing pending local snapshot commit 4795253 onto fetched main
b918711. Conflicts affect collector-health.json, timeframe_signals.jsonl,
latest.json and timeframe-health.json. Runner reported that local observations
were preserved; this invocation stopped before new collection/tests/receipt
import. This closes the unknown failure cause for publication, not recorder state.
No raw NAS log is included in this repository.

Next: run a read-only diagnosis via the existing manually executed BTC Git
Diagnose task (keep its schedule disabled). Under the publisher lock, capture
full HEAD, clean/active-operation state, origin/main divergence and HEAD changed
paths. These determine the exact immutable archive and whether the existing
backup-first recover_pending_snapshot.py contract applies. Current evidence is
insufficient to supply --expected-head or --archive; do not guess them or rerun
a previous incident's repair. No collector restart, reset/clean/force-push,
conflict overwrite or new task. After diagnosis, prepare a guarded recovery;
after actual repair verify a normal NAS upload, quality diagnostics and receipts.
Only aggregate technical findings are public. Validation: actual upload log read
and existing recovery helper prerequisites reviewed; no repair or tests executed.

### NAS evidence audit — 25 October 2026

Read original immutable records and the complete repository tree. Newest published
NAS original remains data/2026/10/25/20261025T083216553390Z-local-1.json
(08:32 UTC / 09:32 Europe/Amsterdam). It verified BOTH provider-side deltas for
04:00–08:00 UTC and had recent journal trades at that historical observation.
It predates #73 and contains no analysis_quality field; no later NAS original
or original numerical mismatch diagnostic was found. That is an evidence/publication
gap, not proof that the recorder has stopped.

Newest original at this read is instead
data/2026/10/25/20261025T175236239465Z-40218548515-1.json:
collection_source=github_fallback, status=ok, cvd_4h=not_collected, reason local
journal not configured, for 12:00–16:00 UTC. Its quality status is degraded:
price_structure available, interval delta unavailable, macro verdict requires
separate evidence. Never reuse the morning NAS delta as this interval's value.

collector-health checked at 17:52:40 UTC says current after reserve recovery
(before stale, outcome uploaded), which establishes market-snapshot recovery
only. Its 24h snapshot coverage was 19/48 half-hour slots (39.6%), with 29 missing.
This is snapshot publication coverage, not trade-recorder uptime or CVD coverage.

The repository tree has ChatGPT receipts but NO data/task-executions/nas receipt
files for watchdog, storage or startup. Their current execution/installation
cannot be confirmed remotely. Read TASK_EXECUTION.md: receipts require a
successful existing NAS publisher import/push; a local spool is not public proof.
Existing runner code preserves pending local commits on conflicts and refuses
dirty trees. Do not reset/rebase manually, restart the recorder or rerun old
incident-specific repairs based on these observations.

Next required external evidence: manually run the EXISTING BTC NAS Collect
Publish task in DSM and inspect its full current task result / first-upload.txt.
If successful, verify a fresh immutable NAS original, #73 diagnostics and
imported receipts. If failed, diagnose the actual error and local Git state
before preparing a targeted repair. No duplicate task, new schedule or runtime
change. No direct authenticated NAS session is available here.
User-facing local time is CET on this date: 08:32 UTC is 09:32 Amsterdam.

Validation: parsed two original JSON records and collector-health, inspected
receipt paths in the complete tree and current publisher/protocol. Documentation
only; no new tests, receipt generation, NAS execution or recovery claimed.

### Restricted DSM schedule observed — 25 October 2026

Supplied Schedule screenshot in watchdog investigation shows Daily, first run
00:00, every 5 minutes, last run 00:55. This configuration only covers the first
hour of each day and cannot provide the intended all-day five-minute watchdog.
The dialog does not show its task title, General/enabled state or script; retain
that identity/configuration boundary. Historical 22:00–22:55 UTC logs are compatible
with a local midnight window before the DST change; do not alter NAS timezone.

Proposed correction for the existing BTC CVD Watchdog: retain Daily, first 00:00
and every 5 minutes; set last run to 23:55 and save. This restores the previously
intended watchdog cadence, adds no task, changes no recorder/runtime or market
schedule. Not yet confirmed saved or executed. Current Task Settings body must
still be inspected for the repository receipt wrapper; schedule correction alone
does not establish receipt installation or publication. Next user action: save
the watchdog time-window correction and send the Task Settings tab screenshot.
Validation: actual visible schedule fields; documentation-only checkpoint.

### Local receipt inventory received — 25 October 2026

Actual read-only diagnosis at 19:07:13 UTC establishes that the expected external
task-executions-pending directory does not exist, and the checkout has zero NAS
watchdog/storage/startup receipt JSONs. There is no local evidence available for
the uploader to import at that observation. This is not proof of a permissions
failure, broken importer, disabled task or stopped collector.

Latest displayed watchdog.log line is 2026-10-24T22:55:01Z (23:55 Amsterdam).
The supplied tail shows five-minute checks only within 22:00–22:55 UTC on the
visible dates; this raises a possible restricted time-window configuration,
but the short historical tail is not authoritative current DSM configuration.
Current wrapper would append a log line and attempt receipt creation on an
ordinary process check. Need current DSM task body, enabled state and full
schedule before editing it or diagnosing why no recent execution is visible.
Earlier reported wrapper replacement does not establish today's task execution.

Next user action: open existing BTC CVD Watchdog in DSM Task Scheduler and supply
screenshots of General/enabled state, Schedule (including first/last run times)
and Task Settings script. Inspect settings first; no task duplication, schedule
change or manual recorder/watchdog start requested. Then diagnose storage using
its actual existing task configuration. Current source-recorded recent trades
remain distinct from watchdog execution status.

Original private log/diagnostic attachment is not copied to this public repo.
Validation: actual diagnostic inventory and timestamps, current wrapper source
and documented task inventory. No code/runtime/schedule changes or new tests.
This supersedes the earlier awaiting-correct-file checkpoint.

### Receipt diagnosis input not yet supplied — 25 October 2026

The newly supplied git-diagnose attachment repeats the earlier 4795253 /
9c165721 divergence and exact original archive listing. It contains no spool
counts or watchdog tail; it is not the requested receipt-diagnose.txt output.
Do not treat it as proof that the recovered conflict has recurred and do not
rerun the old repair. Current receipt diagnosis is still blocked on the actual
/volume1/btc-monitor/receipt-diagnose.txt from the existing manual task.
Next user action: supply that exact file, or run the previously prepared
read-only receipt diagnostic if it has not yet been run. No code/runtime change.
Validation: attachment read and compared with the previous diagnosed identities.

### Pages confirmed; NAS receipt diagnosis required — 25 October 2026

Pages run 40224141712 at NAS head 748ba48 completed successfully; the prior
in-progress deployment checkpoint is closed. Latest published NAS original
remains 20261025T190211916703Z-local-1.json at this read.
Complete current repository tree still contains NO NAS watchdog/storage/startup
receipts. Snapshot/CVD publication works; receipt creation/import remains unproven.
Do not mark these tasks stopped or infer a faulty script from absent evidence.

Reviewed existing watchdog/storage wrappers, receipt writer and importer:
expected private spool is /volume1/btc-monitor/task-executions-pending/nas/TASK;
publisher imports validated six-field receipts and acknowledges after push.
No demonstrated code defect from public evidence. Need read-only local inspection
of spool and checkout receipt presence plus latest watchdog log before changing
a DSM task, permissions or code. Use the existing manual BTC Git Diagnose task;
keep its schedule disabled and preserve all operational tasks/runtime.
No watchdog execution/restart or fabricated receipt is part of this diagnosis.
Public summaries only; do not commit private logs or raw diagnostic output.

Next user action: run the prepared read-only receipt diagnosis in that existing
manual task and provide receipt-diagnose.txt. Next agent action: distinguish
not-created, write/permission/validation failure, import failure or task wiring
from actual evidence, then prepare the smallest justified correction.
Validation: workflow results, complete receipt inventory and current wrapper/
writer/importer source inspection. Documentation-only changes; no new tests.

### Fresh NAS publication restored — 25 October 2026

Remote original NAS records now establish successful ordinary publication:
data/2026/10/25/20261025T185943458441Z-local-1.json and
data/2026/10/25/20261025T190211916703Z-local-1.json.
Both collection_source=nas, snapshot status=ok, cvd_4h status=ok and coverage_verified=true.
The shared CLOSED interval is 12:00–16:00 UTC (13:00–17:00 Amsterdam).
Provider-side spot delta -20.620554 BTC and futures delta +12.8030 BTC are
separate, verified cached evidence; no independent taker/market-wide flow claim.
The newer record finished 19:02:16.902858 UTC (20:02:16 Amsterdam), with recent
spot/futures journal trade timestamps at 19:02:10/19:02:15 UTC.

Both originals contain #73 analysis_quality:
ready_for_scoped_report, scenario_processing consistent, interval delta available,
both markets verified and issues empty. Macro verdict still requires separate
macro evidence; this is not a macro-bottom confirmation. Earlier original mismatch
cause/aggregate investigation remains separate.

The latest supplied log is a DIFFERENT invocation starting 19:00:40 UTC,
not a continuation of the earlier 18:56:46 run. It reports 429 tests passed in
61.040s and both markets verified_cached_evidence. The attached copy itself has
no final EINDSTATUS; successful remote snapshot storage is independently verified.
Do not mistake buffered test fixtures for actual failed NAS receipts or archive loss.

First restored upload head eca11f2 has successful Pages run 40223936047.
Newer head 748ba48 has Pages run 40224141712 in progress at inspection; its
deployment outcome must be rechecked. The repository tree still has NO NAS
watchdog/storage/startup receipt files. Upload/CVD restoration does not close
those hooks, current schedule proof or permanent concurrent-writer resilience.
Next: inspect next scheduled ordinary upload and newest Pages result; diagnose
existing watchdog/storage wrappers/spool using a read-only check if receipts
remain absent. Do not create duplicate tasks or restart the recorder.

These results supersede the pending-upload checkpoints carried from the separate
documentation branch below. Their interim observations are historical.
Validation: two original JSON records, quality/CVD/source/journal times, repository
receipt inventory and commit-specific Pages results. No new tests executed here.

### Tests passed; final upload still pending — 25 October 2026

The next partial log from the same 18:56:46 UTC run confirms 429 tests passed
in 63.410 seconds (OK). It still contains no final EINDSTATUS, CVD pipeline
result, new snapshot or successful push. Remote main remained fa8b1fc when read.
Do not start another run or infer completion/failure from this partial output.

The warning/error simulations, old 08:02 UTC quality JSON, fixture backup/recovery
messages and invalid-receipt messages occur in the test output. In particular
tests/test_task_receipt_sync.py deliberately covers conflicting/invalid receipts
and emits the observed messages. They are not evidence of actual broken NAS
receipts, deleted Elliott history, current source quality or another real repair.
Buffered stdout may appear after unittest's stderr summary. Inspect actual
post-test collection output and original published JSON before diagnosing them.

Interim handover remains on docs/nas-upload-pending-20261025 to avoid moving
main during the active upload. Incorporate both partial checkpoints when actual
completion is known. Validation: partial user result, current runner order,
receipt-test source and remote head; no new local tests or NAS action executed.

### Ordinary NAS upload started; completion pending — 25 October 2026

The supplied partial result starts at 18:56:46 UTC. It confirms successful
synchronization to fa8b1fc and test progress, but ends in progress dots: no test
summary, collection result, push or EINDSTATUS is present. Remote main was still
fa8b1fc at inspection. Do not call this success or failure and do not start a
second run. Await the same run's complete output, then inspect original NAS data
and receipt publication.

This interim checkpoint is saved on docs/nas-upload-pending-20261025, not main,
while the existing NAS task may still be executing. Avoid advancing main during
that task's collection/push window. Incorporate this checkpoint with the final
result after completion; do not use it to trigger another task or recovery.
No executable changes or tests performed here; only the actual partial log and
remote head were inspected. Original private log is not published.

## Next concrete sequence

1. History-to-Pages acceptance observed at 17:53 UTC; see evidence below.
2. Two fresh NAS uploads and both interval deltas verified; recheck newest Pages,
   next scheduled upload and missing watchdog/storage receipts.
3. Perform mobile/browser QA for Elliott and operational status.
4. Separately review draft macroanchor reference/phase; improve independent
   evidence, count substantiation, forward evaluation and upload race resilience.

Recent evidence: Pages 40202767429 and 40202849481 succeeded. History
40202144771 succeeded. Health 40201722831 failed, then 40202113500 succeeded;
retain both results. Latest full implementation validation reported in #75:
429 Python tests, five Node status tests, read-only staging and SVG inspection.
#76 reported YAML/trigger checks and ten history tests. These are dated results,
not tests newly executed for this documentation-only update.

Open PRs when checked: #2, #3, #4, older proposals. #64–#76 are merged.
Source details: [ELLIOTT_HISTORY.md](ELLIOTT_HISTORY.md),
[CVD_RECONCILIATION.md](CVD_RECONCILIATION.md),
[QUALITY_CONTROL.md](QUALITY_CONTROL.md), [TASK_EXECUTION.md](TASK_EXECUTION.md).

### History completion acceptance — 25 October 2026, 18:53 Amsterdam

Observed history run [40218583040](https://github.com/Cravendor/btc-monitor/actions/runs/40218583040)
completed successfully at 17:53:03 UTC. Pages run
[40218606715](https://github.com/Cravendor/btc-monitor/actions/runs/40218606715)
was created at 17:53:05 UTC with event=workflow_run and updated archive head
62df549; staging, quality gate, artifact upload and deploy-pages all succeeded
(completed 17:53:34 UTC). The earlier health-triggered Pages run was already
created at 17:52:48 UTC, alongside history, so this is a distinct later completion
run. With the #76 workflow configuration, timing and updated head, the observed
chain supports operational acceptance of automatic history-to-Pages publication.
The source-run ID is inferred from these records; the API run listing does not
expose the triggering event payload. This is not continuous-availability proof
or a new browser/mobile visual inspection.

coverage.json checked 17:52:57 UTC: 68 weekly / 481 daily / 2,890 4H / 11,561 1H
candles; all degrees complete with zero missing candles at that checkpoint.
Checked cross-degree prices and base volumes remain consistent.
No executable, schedule, NAS task or data change was needed. Validation consisted
of actual run/job/step results, workflow configuration and original coverage JSON.
Handover/status links and whitespace checked. No new runtime tests claimed.
Next: inspect a fresh original NAS snapshot for quality/recovery diagnostics and
watchdog/storage receipt publication; preserve strict per-interval validation.

## Constraints and maintenance

EUR 0; public APIs; Bitget BTCUSDT USDT-FUTURES in USDT primary. Missing is
unavailable, never zero/neutral. Closed candles, explicit source/time provenance,
exact CVD volume checks. Preserve snapshots, original reports, versions and NAS
journal/runtime. General context only, no orders or private portfolio tracking.
Schedules/runtime must be checked in their actual service; this document does
not establish current automation settings.

After every executed task, update HANDOVER and this status before reporting
completion, including results of external runs. Update DECISIONS for changed
accepted rules. Record implemented, merged, deployed and observed separately,
with evidence, remaining uncertainty and next step. No private transcripts,
IDs, credentials, raw journals or NAS logs in the public repository.
