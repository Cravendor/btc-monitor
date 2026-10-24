# BTC monitor — agent handover

Checkpoint: 24 October 2026, Europe/Amsterdam. This is a curated technical
handover, not a complete transcript or private-chat export. Read together with
[PROJECT_STATUS.md](PROJECT_STATUS.md), [DECISIONS.md](DECISIONS.md) and current
code/data. Repository: [Cravendor/btc-monitor](https://github.com/Cravendor/btc-monitor).
Dashboard: https://cravendor.github.io/btc-monitor/.

## Resume from here

PR #63 merged on 24 October at 23:23 Amsterdam: multi-year daily history,
361 tests and 2,122 live-fetched closed days. Its initial history workflow and
Pages publication both completed successfully. Verify the next NAS coverage
metadata separately; merging source data does not prove NAS incorporation.
Next feature: adapt the complete historical source into the opt-in cycle-anchor
context with an explicitly justified previous completed-cycle peak and phase.
Do not automatically activate the new macroanchors from data coverage alone.

The current user preference is to retain the observed-history anchors until
the macro policy has adequate evidence. Latest accepted rule is price-event
based; the earlier fixed bear-calendar-year proposal was superseded.

## Implemented versus activated

| Component | Evidence/checkpoint | Remaining limitation |
| --- | --- | --- |
| NAS market snapshots | Restored uploads confirmed 24 October at 22:01 and 22:33 Amsterdam, then a 23:01 NAS snapshot observed | Continuous availability not guaranteed; recheck latest source and statuses |
| Public homepage and meters | PRs #56–#61 merged; Pages checked after #60/#61 | New browser visual QA still outstanding; HTML retrieval/tests are not interactive visual QA |
| Two public routes, five directional readings each, 25 ordered combinations | PR #60 merged; original swing/position assessments frozen and validated in NAS data | Combination-specific performance statistics not complete |
| Observed-history anchor candidates | PR #61 merged; v4 source snapshots observed after merge | Available native history was only about 89 daily/36 weekly candles; not verified cycle extremes |
| Macro policy: cycle peaks and running lows | PR #62 merged, CI successful; opt-in v5 contract and hooks exist | No automatic cycle identification or fresh multi-year context producer; NOT ACTIVE by default |
| Multi-year daily source | PR #63 merged; CI, initial history workflow and Pages success | Next NAS coverage metadata still to verify |
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

1. Verify the next NAS cycle_history_reference now that #63 and its initial workflow are complete.
2. Connect the multi-year archive to cycle_anchor_context, with justified prior
   completed-cycle peak/phase and current closed source coverage. The numerical
   selector is prepared, but no producer or autonomous phase detection is active.
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
