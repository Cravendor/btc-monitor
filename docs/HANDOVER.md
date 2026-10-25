# BTC monitor — agent handover

Current checkpoint: 25 October 2026, Europe/Amsterdam. This is a curated technical
handover, not a complete transcript or private-chat export. Read together with
[PROJECT_STATUS.md](PROJECT_STATUS.md), [DECISIONS.md](DECISIONS.md) and current
code/data. Repository: [Cravendor/btc-monitor](https://github.com/Cravendor/btc-monitor).
Dashboard: https://cravendor.github.io/btc-monitor/.

## Current handover — 25 October 2026, Europe/Amsterdam

This section and PROJECT_STATUS.md supersede older preparation/open-PR wording
below. Original entry point was created in commit 0ab7fde on 24 October at
21:31:28 UTC (23:31 Amsterdam). Reconciled against repository history through
48191e8 and merged PRs #65–#76. This is a curated evidence record, not a transcript.

### Watchdog corrected settings reviewed; save/execution pending — 25 October 2026

New screenshot shows the enabled BTC CVD Watchdog row and editor schedule:
Daily, first 00:00, every 5 minutes, last 23:55. User supplied current script
command /bin/sh /volume1/btc-monitor/repo/nas/cvd_watchdog.sh, matching reviewed
wrapper. This closes schedule/body review; editor is still open, so saving and
a new real execution/receipt are not yet proven. No need to replace this script
or create another task.

Next user action: click OK to save, allow the next five-minute scheduled check,
then run the existing read-only receipt diagnostic via BTC Git Diagnose and
supply updated receipt-diagnose.txt. Do not manually restart the collector.
Confirm a recent watchdog log/receipt locally, then publication by the existing
half-hour NAS uploader; storage configuration remains separate open work.
Validation: visible corrected settings and supplied exact command only;
documentation checkpoint, no actual DSM mutation, execution or tests by agent.

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

### Completed since the entry point was created

| Change | Confirmed result | Remaining boundary |
| --- | --- | --- |
| #64 / #66 handover | Mandatory entry point and technical handover merged; post-merge context refreshed | Read current repository evidence each session |
| #65 cycle-context producer | Merged 46dd127; original 00:40 Amsterdam NAS draft review verified | Macroanchor configuration remains draft; no automatic cycle identification or activation |
| #67 Dutch explanations | Merged 487310f; Pages run 40138890905 succeeded and translated labels observed | Does not change stored assessments |
| #68 operational status | Merged 8b85900; task-status page and separate evidence states implemented | Colour is evidence/freshness, not continuous process proof |
| #69 execution receipts | Merged 17f9698; minimal receipts and per-task cards implemented; actual monitor receipts subsequently committed | Not every scheduled run or DSM hook proven |
| #70 watchdog wrapper | Merged cd884a5; receipt spool/import and process checks added; wrapper replacement reported | Recheck first/current public receipt; preserve existing task schedule |
| #71 pending upload repair | Merged 79fc0bb; real NAS recovery c4e2e94 preserved original observation and both histories | One incident repaired; concurrent-writer resilience still open |
| #72 storage wrapper | Merged 43fd3dc; safe storage-check receipt support | Installation and first receipt not established by merge |
| Ordinary NAS uploads | Recovery followed by successful upload, EINDSTATUS 0, 401 tests in supplied result; commits 03ce980 and 57d7173 present | NAS collection and Pages publication remain separate |
| #73 CVD diagnostics / quality gates | Merged 6d8b71d; exact validation, bounded same-candle retry, safe aggregate diagnostics, report/dashboard quality gates | Post-merge NAS uptake and real scheduled-task compliance need separate evidence |
| #74 Elliott visuals | Merged 09be532; bull/bear candidates at week/day/4H/1H, eight charts, anchor/rule/zone evidence | Provisional candidates; not proved current count, nested subwaves or calibrated rejection strength |
| #75 long Elliott history | Merged bf8a61e; complete native history from July 2025, resumable collection and incremental update observed | Longer source scope does not certify a count |
| #76 history-to-Pages completion | Merged bd80bd3; Pages now watches BTC multi-year daily history completion | Operational chain observed: history 40218583040 → Pages 40218606715; see acceptance above |

### Correct CVD interpretation

The 08:02 UTC rejection for 04:00–08:00 UTC was followed by an original 08:32 UTC
NAS snapshot (57d7173, data/2026/10/25/20261025T083216553390Z-local-1.json)
verifying BOTH markets exactly. Independent public-history replay matched BTC
and USDT volumes as well: spot 12,270 trades, delta -4.374325 BTC; futures
47,160 trades, delta -223.2247 BTC. See CVD_RECONCILIATION.md.
Do not carry the earlier mismatch forward as a current blanket failure.
The original discrepancy remains unquantified until its saved numerical
diagnostics are inspected; cache lag is only a hypothesis. Historical 49/84 gap
counters are not new failures in every interval. Provider-side trade delta is
not independently verified aggressor-side or market-wide CVD. Exact validation
remains mandatory for each interval; no arbitrary tolerance.

### Source and publication evidence

coverage.json checked 2026-10-25T14:25:22.242273+00:00 records zero gaps:
68 weeks, 481 days, 2,889 4H and 11,558 1H candles. Requested start is
2025-07-01 UTC, with the weekly candle beginning 2025-06-30 included.
All checked parent price/base-volume groups match; normalized quote differences
are diagnostic only and do not relax CVD equality. Source end times differ by
degree. See ELLIOTT_HISTORY.md and data/history/elliott/coverage.json.

The earlier live checkpoint in ELLIOTT_HISTORY.md records complete sources and
eight charts at 14:20:29 UTC. This session checked successful Pages runs
40202767429 (head bd80bd3, after #76) and 40202849481 (head 48191e8).
History runs 40201722874, 40201739696 and 40202144771 succeeded.
Health run 40201722831 failed; later 40202113500 succeeded. Do not erase the
failed execution or infer permanent recovery from one later success.
A successful deployment is not new browser/mobile QA or proof of the exact
workflow_run trigger path. No authenticated NAS access is available here.

### Next concrete steps

1. History completion publication accepted for the observed run above.
2. Inspect a fresh original NAS snapshot for #73 quality/recovery diagnostics;
   retrieve original mismatch totals if still missing. Verify current receipt
   publication for watchdog/storage; obtain existing startup body only when needed.
3. Actual mobile/browser QA of Elliott and status panels; existing desktop/SVG
   checks do not close this.
4. Separately review macroanchor activation, independent macro/news evidence,
   Elliott nesting and psychology, forward evaluation and concurrent writers.
5. Open PRs at this read: #2, #3, #4 (older proposals). They are not deployments;
   compare scope before reusing. #64–#76 are merged, not pending review.

### Maintenance after every executed task

Before reporting a task complete, update this handover and PROJECT_STATUS in the
same change, or immediately after an external execution/result is observed.
Record task/result, changed files, validation, PR/commit, merged/deployed/observed
states, blockers and next step. Update DECISIONS for changed accepted rules.
A task producing no code still needs its outcome recorded when material.
Never fabricate receipts, future results, deployment proof or retrospective tests.
Preserve original observations; publish only public-safe technical summaries.

Documentation reconciliation validation: read the current four handover files,
PR #73–#76 records, history coverage, Pages workflow and recent Actions results;
checked internal handover links and superseded-state consistency. No executable,
schedule, NAS task or data changes; no new runtime tests claimed.

## Historical checkpoints (superseded where the current section differs)

The following sections retain earlier observations and preparation history.
Their “open”, “not merged”, “next” and “not deployed” statements apply to their
original checkpoint only; use the current section above to resume.

## Earlier resume checkpoint

Post-merge checkpoint: 25 October 2026, Europe/Amsterdam.

## New checkpoint: operational task status

The accompanying change builds btc-status.html, linked near the top of the home
page. Read [OPERATIONAL_STATUS.md](OPERATIONAL_STATUS.md) for its evidence contract,
freshness windows, free public GitHub API use and validation. NAS upload, spot/
futures journal evidence, stored-market health and GitHub jobs remain distinct.
Unconnected DSM watchdog/storage and ChatGPT execution status are grey, not an
invented stopped/running state. Local checks: 378 Python tests, five Node tests,
home/status generation and diff/link checks. Deployment, browser API access and
mobile visual QA must be checked after merge; the page is not live yet.

The NAS retry succeeded: original 00:32 and fresh 00:40 Amsterdam observations
are now on main (e820048). The 00:40 record is status=ok and contains the original
ready draft macroanchor review, plus recent journal trades in both markets.
This closes the #65 original automatic-review storage check. The macroanchor
configuration still remains draft; do not activate it as part of a status page.

PR #67 publication succeeded (Pages run 40138890905) and the translated zone
explanation was observed live after refresh. The commit-specific workflow helper
had returned an empty list; repository Actions runs API supplied the actual runs.
Earlier statements below about unverified publication/storage are historical
checkpoints superseded by this evidence. Future writer races remain possible.

Next: review/merge/publish this status page, verify its live data and API failure
behaviour, then obtain actual mobile visual QA. Do not create duplicate NAS tasks.

Browser checkpoint: the live desktop page was inspected at a 1348px viewport.
Swing/position switching, both position route disclosures and their ladders,
and navigation to the multi-timeframe page worked. No whole-page horizontal
overflow was present with both position routes open. This is partial desktop
visual/interaction QA, not iPhone QA or proof of #65 deployment: the latest
visible snapshot still ended 2026-10-24T22:01:55.667737+00:00, before #65.
The browser API used here does not expose viewport emulation, so mobile QA is
still open. Only an extension-origin metadata error appeared in captured logs;
it was not a dashboard script error.

The zone explanation visibly exposed `undecided`. The accompanying rendering
change translates all six reaction codes and the new macro review phase/state
labels to Dutch without changing stored assessments, anchors or model versions.
Publication and another live check of those new labels remain separate steps.

PR #63 is merged and its source metadata is now verified in an original NAS
snapshot ending 2026-10-24T22:01:55.667737+00:00: 2,122 closed days, no gaps,
through 2026-10-23. This closes the previous metadata-incorporation check.

PR #65 is merged (merge commit 46dd127): a read-only producer connects the archive to a separately stored
cycle_anchor_review, with explicit prior reference window, phase rationale,
configuration/archive hashes and local-versus-network timestamps. Its shipped
configuration is draft, so existing v4 routes remain unchanged. A separately
reviewed active configuration supplies original v5 context; incomplete history or
invalid active configuration suppresses readings without short-range fallback.
369 local tests, read-only dashboard generation and GitHub validation pass
(Actions run 40137999451). Post-merge Pages publication and an automatic NAS review must still be
verified separately; the latest observed NAS snapshot predates this merge.

The draft proposes the first highest Bitget futures daily high within 2021
(2021-11-10) as prior reference and post_peak as an operational price-route
hypothesis; it does not identify all cycles or confirm that the latest top is
final. Do not activate merely because this proposal or complete data exists.
Next: verify post-merge Pages publication and a new original NAS draft review,
then review the proposed reference/phase.
Read docs/CYCLE_CONTEXT.md from #65 when that change is available.

PR #64 is merged (7cd2b1a); its later branch-only documentation update is
superseded by this post-merge checkpoint. The accepted rule is
price-event based; the fixed bear-calendar-year proposal was superseded.

## Implemented versus activated

| Component | Evidence/checkpoint | Remaining limitation |
| --- | --- | --- |
| NAS market snapshots | Restored uploads confirmed 24 October at 22:01 and 22:33 Amsterdam, then a 23:01 NAS snapshot observed | Continuous availability not guaranteed; recheck latest source and statuses |
| Public homepage and meters | PRs #56–#61 merged; live desktop interaction/visual checks recorded above | Mobile QA and post-#65 deployment/original NAS review still open |
| Two public routes, five directional readings each, 25 ordered combinations | PR #60 merged; original swing/position assessments frozen and validated in NAS data | Combination-specific performance statistics not complete |
| Observed-history anchor candidates | PR #61 merged; v4 source snapshots observed after merge | Available native history was only about 89 daily/36 weekly candles; not verified cycle extremes |
| Macro policy: cycle peaks and running lows | PR #62 merged, CI successful; opt-in v5 contract and hooks exist | No automatic cycle identification; #65 adds the guarded producer, with draft configuration |
| Multi-year daily source | PR #63 merged; complete coverage metadata verified in the 22:01:55 UTC NAS snapshot | Next UTC day still requires fresh archive coverage |
| Archive/context producer | Merged PR #65; 369 local tests and read-only generation pass | Draft review only; CI passed; deployment and original NAS review still to verify |
| Technical signal history/evaluation | Existing JSONL and statistics/evaluation modules | Same-price-source heuristics are uncalibrated |
| Original monitor report archive | Reports present on main for 4h-warning and psychology; protocol v2 | Not every scheduled execution or report type proven; read actual archive |
| CVD journal/export/backfill | Existing recorder, sessions, coverage verification and bounded recovery | Per-market/interval proof required; no independent aggressor-side or market-wide CVD claim |
| News and psychological reports | Separate reports/automation and homepage context | No validated numerical news score in two-route readings; no proved current Elliott count or psychological phase |

## Accepted product and analysis behavior

Budget EUR 0. Bitget is primary. Label exchange, market, instrument, currency,
timeframe, observation time and source time. Secondary venues are explicitly
secondary; Coinbase premium is a Bitget comparison proxy, perpetual mark/index
premium is not a dated-futures annualized basis. Limited book depth does not
prove passive absorption. Missing sources are not zero/neutral or an alert.

The monitor tests competing hypotheses: macro bottom/absorption versus complacency
bounce/distribution. Separate short-term reactions from macro bottom confirmation.
Historical analogies (including 2021–2022) are context, not proof. BUY means upward
evidence and SELL downward evidence in BOTH public routes, never secretly opening
a short in the bear route. Five states: strong SELL, SELL, neutral/wait, BUY,
strong BUY; missingness is outside these five. Same-source agreement is not two
independent confirmations. No personal trade/position/stop state or TP percentage.

Swing uses native day momentum/zone context; position uses native week context.
Closed 4H reactions may provide timing. Timelines are price paths with attention
zones/current-price markers, not predicted arrival dates or confirmed historical
route execution. Retest labels require actual crossing and re-touch evidence.
Elliott price-pattern candidates do not establish internal subwaves; psychology
is explicitly a hypothesis unless independently supported. See method docs.

## NAS task inventory — do not create duplicates

Hardware/runtime checkpoint: DS415+, DSM 7.1.1 Update 9. Periodic publisher uses
Python 3.9.14 at `/usr/local/bin/python3.9`. Continuous CVD recorder has a separate
older venv under `/volume1/btc-cvd/venv`; do not replace it just to run publisher
tests. Dedicated Git checkout: `/volume1/btc-monitor/repo`.

| Task/name | Function | Confirmation and uncertainty |
| --- | --- | --- |
| BTC NAS Collect Publish | Normal collection, scenario freeze, archive and GitHub upload | User tony, every 30 min 00:00–23:30; creation confirmed 23 October; enabled again after 24 October repair, uploads confirmed |
| BTC CVD 24H Collector | Continuous spot/futures trade recorder/start mechanism | Exists and previously ran as tony; historical daily/boot arrangements varied, so recheck actual enabled state rather than infer it |
| BTC CVD Watchdog | Checks/restarts recorder | Every five minutes; user confirmed enabled; later DSM screenshots show watchdog enabled |
| BTC Collector Process Check | Reads process list into process-check.txt | Diagnostic only; neither recorder nor dashboard publisher |
| BTC Git Diagnose | One-time diagnostic, later used to launch repair script | Created during this session; keep disabled after manual use |
| BTC CVD Stor… / Auto… and other abbreviated DSM rows | Storage/start or diagnostic tasks were visible in earlier screenshots | Full names and scripts not completely verified; do not guess or delete them |

`nas/collect_publish.sh --run` is the publisher, not
`bitget_cvd_collector.py`. Continuous recorder writes trades.sqlite3, health.json,
collector.log and owns its lock in `/volume1/btc-cvd`. Publisher lock is separate
under `/volume1/btc-monitor`. Read [NAS.md](NAS.md) before changing anything.
No direct authenticated NAS session is available here. User-provided logs and
remote GitHub data do not establish current DSM process state.

The user often uses iPhone Safari/DSM. For diagnostics prefer inspecting an
existing task/result or a disabled, explicitly one-time diagnostic. Preserve
original task scripts. A DSM result showing no output may reflect redirection
into first-upload.txt, not absence of activity. Read the complete newest log.

## Recovered Git incident

Local NAS commit 252a205 held a dated 16:31 measurement; GitHub had separately
updated generated views and signal history. Rebase conflicted in latest.json,
collector-health.json, timeframe-health.json and timeframe_signals.jsonl. The
runner aborted the rebase and retained the observation. A clean worktree did
NOT mean the branches were synchronized.

A one-time tested recovery made a verified local Git bundle, merged both commit
histories, retained the dated original snapshot unchanged, combined historical
signal rows, kept upstream generated views and pushed normally. Remote merge
commit a64adc1838fa266c5808dd72b9a2b14bdd0ad333 confirms recovery. Backup filename
on NAS: recovery-252a205.bundle outside the checkout. Later NAS uploads succeeded.
Do not rerun the old repair script: it is bound to the old exact HEAD and should
refuse a changed state. Recurrent concurrent-writer conflicts are still a
resilience improvement, not fixed generically by this one-time repair.

## Three separate automation layers

1. NAS DSM tasks: local journal and periodic publisher; inventory above.
2. GitHub Actions: tests, Pages, collector freshness reserve, technical/report
   archive processing; see actual `.github/workflows/*.yml` on main.
3. ChatGPT automations: market analysis/alerts and Quality & Improvement; inspect
   their current state privately via the connected automation service when needed.
   Do not put task IDs, conversation IDs or private prompt contents in this repo.

Actual automation settings read on 24 October (not changed by this handover):

| Title | State | Recorded schedule |
| --- | --- | --- |
| BTC 4H en dagrapport | Enabled | 00/04/08/12/16/20 Europe/Amsterdam; 08 report is the daily edition |
| BTC psychologie en scenario’s | Enabled | 08:00 Europe/Amsterdam from 25 October; older protocol text still says 12:00 |
| Breaking Market Risk Alert | Enabled | Hourly condition checks; original material-change rules apply |
| VIX Below 30 Alert | Enabled | Daily; preserve actual existing schedule/threshold |
| BTC Quality & Improvement | Enabled | First day monthly at 08:00 Europe/Amsterdam; quarterly review in Apr/Jul/Oct, annual review in Jan, within the same task |
| BTC 4H Early Warning | Paused | Superseded separate task; do not recreate it from old chat instructions |

Five enabled automations were returned including Quality & Improvement. Older
PROJECT_STATUS/protocol statements describing four active monitors refer to a
previous count/category grouping. The monthly QI task had no recorded run yet.
Schedule configuration is not proof of execution/delivery. Some QI prompt text
still describes older four-route versions and protocol v1; a later design clause
covers two routes, but always reconcile actual code/archive protocol (currently
v2) before use. Do not silently edit schedules or automation prompts as part of
an unrelated implementation. Document/resolve discrepancies in the relevant task.

## Code and data map

| Need | Main locations |
| --- | --- |
| Market collection | scripts/collect.py, enrich.py, multi_timeframe_collector.py, native_timeframe_candles.py |
| Latest and immutable original measurements | data/latest.json (newest first); data/YYYY/MM/DD/*.json |
| Source/archive health | data/collector-health.json, data/timeframe-health.json, scripts/history_coverage.py |
| Technical signals and history | scripts/multi_timeframe_signals.py, timeframe_signal_history.py; data/history/timeframe_signals.jsonl |
| CVD | scripts/bitget_cvd_collector.py, cvd_store.py, cvd_export.py, cvd_backfill.py, cvd_coverage.py, cvd_pipeline.py |
| Public root and meters | scripts/home_dashboard.py, market_gauges.py, two_routes.py, swing_dashboard.py |
| Scenario calculation/freeze | scripts/swing_scenarios.py, scenario_archive.py, route_anchors.py, cycle_anchor_policy.py |
| Technical/scenario outcomes | scripts/scenario_evaluation.py, signal_outcome_validation.py, signal_statistics.py |
| Original monitor reports | reports/inbox/, reports/YYYY/MM/DD/, reports/index.json; scripts/monitor_archive.py, report_context.py |
| Multi-year archive | scripts/cycle_history.py; data/history/bitget_btcusdt_daily.json; .github/workflows/cycle-history.yml |

The public root is generated by Pages; repository index.html is the underlying
market dashboard copied to btc-dashboard.html during staging. Do not assume
editing only index.html changes generated root meters. `btc-action-history` is a
legacy filename for scenario/level outcomes, not personal action/trade history.
Four internal older scenario definitions remain for historical compatibility;
there are TWO public routes. Do not delete old records or count repeated legacy
outcome rows as independent two-route observations.

## Documents to read for the task

- [NAS.md](NAS.md): runtime, SSH configuration, task runner, publication behavior.
- [CVD.md](CVD.md): sessions, backfill, provider-scoped coverage and hard limitations.
- [MARKET_GAUGES.md](MARKET_GAUGES.md): versioned meter/route/anchor rules; later
  sections supersede historical four-route descriptions where explicitly stated.
- [INTERPRETATION_LAYER.md](INTERPRETATION_LAYER.md): method and uncertainty; some
  descriptions are specifically the retained 4H range layer, not current 1D/1W UI.
- [MONITOR_ARCHIVE.md](MONITOR_ARCHIVE.md): CURRENT report ingestion protocol,
  privacy, report types and exact immutable text. Read actual version before writing.
- [BIAS_HISTORY.md](BIAS_HISTORY.md): psychological report/history context.
- [CYCLE_HISTORY.md](CYCLE_HISTORY.md): separate resumable daily archive, provenance, coverage and workflow.

## Open work, in practical order

1. Verify post-merge #65 Pages publication and its original automatic NAS draft review.
2. Review the proposed prior reference/phase and current closed source coverage;
   activate separately only when justified. The producer is built in #65, but its
   shipped draft preserves current anchors; autonomous cycle recognition is absent.
3. Integrate independently sourced news/macro evidence into tested route logic;
   current news reports are context, not numerical route votes.
4. Further substantiate current Elliott alternatives and psychological phase;
   preserve unavailable status rather than invent a count or phase.
5. Build dedicated two-route/25-combination forward outcome analysis and sufficient
   7/30/90-day follow-up, separated by original versions, with honest missingness,
   dependent samples, conflicting interpretations and no personal trading returns.
6. Actual mobile/desktop browser visual/interaction QA for recent features.
7. Structural mitigation of NAS/GitHub simultaneous-writer upload conflicts;
   preserve observations and avoid force-push/destructive checkout recovery.
8. Reconcile documented versus actual monitor schedule/protocol version claims
   when those automations are next maintained; do not create duplicates.

Last full code validation: 354 tests on merged #62; 361 on merged #63 plus successful
CI/read-only generation. Counts are checkpoints, not promises for future versions.
For this handover-only change validate links and status consistency; no executable
behavior changes are intended.

## Handoff rule for every subsequent agent

Update this document after meaningful changes, together with live evidence and
open PR status. Keep decisions separate from transient measurements. A merge,
Pages success, inspected HTML, real browser test and an original NAS snapshot are
different evidence; report each only when actually checked. Fresh session access
to this repository is necessary: chat memory alone cannot guarantee continuity.

## Execution evidence checkpoint — 25 October 2026

Prepared a strict minimal task receipt protocol in [TASK_EXECUTION.md](TASK_EXECUTION.md),
reader/writer in scripts/task_execution.py and status-page integration. Each
connected ChatGPT monitor/QI task gets its own card. The newest receipt controls
status, including errors or invalid evidence; stale success expires. Startup
receipts do not prove a running process. Existing Pages builds on receipt pushes.
No new scheduled task, market alert, DSM script change or fabricated receipt.

The actual automation service was read this session: the three BTC monitors and
Quality & Improvement already contain protocol-gated receipt instructions; QI
also includes operational failures/recovery in its existing review. Schedules
were not changed. Protocol was not yet on main when checked, so public execution
is not yet proven. VIX is outside this connection. No private automation IDs or
prompts are included here.

Next: merge/publish this change, then inspect real new receipts and live cards.
NAS watchdog/storage/start hooks require the actual existing DSM script contents
and task names, followed by reviewed staging/publication integration. Reader and
writer support are prepared only; those tasks remain unconnected until then.

Validation for this checkpoint: 386 Python tests, five Node status-transition
tests, read-only status generation and git diff whitespace checks pass locally.
PR/CI/deployment evidence must be checked separately.

Open implementation PR: [#69](https://github.com/Cravendor/btc-monitor/pull/69).
At creation, GitHub validation run 40165487142 was in progress; recheck its
final result before claiming CI success. Not merged or deployed at this checkpoint.

## Watchdog integration preparation — 25 October 2026

PR #69 is merged; live status JSON has individual cards, with no execution
receipts at the last check. The user supplied the actual DSM watchdog body.
Prepared nas/cvd_watchdog.sh preserving its recorder/flock/runtime paths,
adding process-presence confirmation and minimal completion/error receipts.
External spool plus strict import/post-push acknowledgement is added to the
existing NAS publisher. The watchdog freshness tolerance is now 45m because
five-minute checks are published by the existing half-hour task; no new schedule.
See TASK_EXECUTION.md for installation order and exact existing-task command.
Not installed or observed on NAS yet. Storage/startup scripts still unknown.

Validation: 392 Python tests, five Node status tests, shell syntax for both NAS
scripts, read-only status generation and diff checks pass locally. CI, merge,
DSM installation, first receipt and publication remain separate checkpoints.

Implementation PR [#70](https://github.com/Cravendor/btc-monitor/pull/70) is open.
Recheck its CI, merge and actual NAS installation before describing it as active.

## Pending NAS upload recovery — 25 October 2026

PR #70 is merged, but a supplied NAS diagnosis shows the publisher checkout has
one pending snapshot commit and a clean tree diverged from upstream. It has not
yet demonstrated receipt integration or watchdog installation. Prepared the
explicit nas/recover_pending_snapshot.py helper; see NAS.md for safeguards and
execution through the existing manually run diagnostic task. The original
observation and both histories must remain intact. Local Git-fixture tests cover
success and refusal/abort/rejected-push paths. No actual NAS repair or new upload
is established by these tests. Next: review/helper execution, inspect repair log
and a fresh ordinary NAS upload, then resume watchdog installation. No duplicate
DSM task, force-push or collector/database restart.

Recovery implementation is open in [PR #71](https://github.com/Cravendor/btc-monitor/pull/71).
397 Python and five Node tests pass locally. Recheck current CI, merge and actual
NAS repair outcome; none is implied by this preparation checkpoint.

## Storage receipt preparation and recovery checkpoint — 25 October 2026

The previous NAS recovery is confirmed by the external task result and remote
merge c4e2e94: the original pending NAS snapshot is on main, together with both
signal histories and new code. This closes one recovery incident, not the
concurrent-writer resilience issue. The user confirmed replacing the watchdog
body with the repository wrapper. First real watchdog receipt/new ordinary NAS
upload was still unverified at the latest read; no process availability inferred.

The user supplied the storage ls/du/date body. Prepared nas/cvd_storage_check.sh
and execution tests with no database changes; see TASK_EXECUTION.md. Script/report
failures must not become success via the last date command. Full existing task
name/schedule still unknown; preserve them at installation. Storage installation,
first public receipt and live status are unverified. Startup script remains needed.

Prepared in [PR #72](https://github.com/Cravendor/btc-monitor/pull/72); not installed.
401 Python tests, five Node status tests, shell syntax and diff checks pass locally.
Recheck final CI, merge, original NAS receipt and live page separately.
