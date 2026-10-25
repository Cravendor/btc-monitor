# BTC monitor — agent handover

Checkpoint: 24 October 2026, Europe/Amsterdam. This is a curated technical
handover, not a complete transcript or private-chat export. Read together with
[PROJECT_STATUS.md](PROJECT_STATUS.md), [DECISIONS.md](DECISIONS.md) and current
code/data. Repository: [Cravendor/btc-monitor](https://github.com/Cravendor/btc-monitor).
Dashboard: https://cravendor.github.io/btc-monitor/.

## Resume from here

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
