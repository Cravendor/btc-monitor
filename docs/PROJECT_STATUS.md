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

## Next concrete sequence

1. History-to-Pages acceptance observed at 17:53 UTC; see evidence below.
2. Diagnose pending local commit 4795253 via the existing manual Git task;
   prepare guarded recovery, then verify a fresh NAS original and receipts.
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
