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
| History completion to Pages | #76 merged; explicit trusted completion trigger present; post-merge Pages successful | Actual post-merge history-completion → Pages chain still to observe |
| Original reports/history | Immutable archives and execution receipts have actual commits | Not proof that every planned report ran/delivered |
| Macro/news and psychology | Contextual reports and candidate rules exist | No validated independent numerical macro/news vote or certified phase |
| Forward evaluation | General technical/scenario tooling exists | Dedicated two-route/25-combination analysis and sufficient 7/30/90-day follow-up |
| Visual QA | Prior desktop interaction, SVG checks and live quality checkpoint recorded | New full browser/mobile interaction QA remains open |

## Next concrete sequence

1. Verify the next real history-completion → Pages chain after #76.
2. Inspect fresh original NAS quality/recovery fields and original mismatch
   diagnostics; verify watchdog/storage receipt publication without duplicating tasks.
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
