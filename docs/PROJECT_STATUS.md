# BTC Monitor — current scope and open work

Checkpoint: 24 October 2026, Europe/Amsterdam. Start with [HANDOVER.md](HANDOVER.md)
and [DECISIONS.md](DECISIONS.md). This replaces earlier same-day wording such as
"this change/in review" that no longer described merged releases accurately.
Current GitHub code, actual original data, PR states and run results override this
checkpoint when they change.

| Component | State at checkpoint | Practical limit |
| --- | --- | --- |
| Operational task status | Built in accompanying change; 378 Python + 5 Node tests and read-only generation pass | Not deployed yet; DSM watchdog/storage and ChatGPT runtime remain explicitly unconnected |
| NAS publisher | Restored; successive NAS uploads and Pages publication verified | Concurrent upstream writes can still reject a push |
| Continuous CVD / sessions / backfill | Existing implementation and earlier successful NAS operation | Verify each market/interval; no market-wide or independently verified aggressor-CVD claim |
| Technical multi-timeframe signals/history | Implemented | Provisional price/volume rules; not integrated independent macro evidence |
| Public meters | Two public routes with five directional states and combined interpretation, merged #60 | No private position state or calibrated probabilities |
| Available-history route anchors | Merged #61; v4 records observed | Native day/week windows are not verified cycle extrema |
| Cycle-top/running-low rule | Merged #62; 354-test CI success | Explicit cycle/phase required; producer merged #65, default remains draft |
| Multi-year daily archive | Merged #63; 2,122 source-validated closed UTC days through 2026-10-23; NAS coverage metadata verified at 22:01:55 UTC | Fresh coverage required at each new UTC day |
| Archive to cycle-context producer | Merged PR #65; ready draft review verified in original 00:40 Amsterdam NAS record | Macroanchor activation remains a separate reviewed change |
| Original report archive | Protocol v2, real 4h-warning and psychology records observed | Read current protocol, not old automation prompt version claims |
| News integration | Separate contextual reports | No validated numerical news contribution to route scores |
| Elliott/psychology | Rule checks/candidates and phase hypotheses | No complete proved current wave count or automatic psychological phase |
| Forward result evaluation | General technical/scenario tooling exists | Dedicated two-route/25-combination evidence and enough 7/30/90-day follow-up still needed |
| Visual QA | Live 1348px desktop check: swing/position toggle, both position routes/ladders and timeframe navigation work; no whole-page horizontal overflow with routes open | iPhone/mobile QA, new-label verification and post-#65 deployment/original NAS review remain open |
| Quality & Improvement | Existing enabled monthly task, with quarter/year levels | No recorded QI run at the checkpoint; old prompt clauses need version-aware interpretation |

## Next concrete sequence

1. Review/merge/publish the operational status page; verify live evidence/API access and mobile layout. Original #65 NAS draft review and #67 Dutch label are now verified; see HANDOVER.
2. Review the proposed reference window/peak and operational phase; activate in a
   separate reviewed configuration change when justified. Current anchors remain
   active with the shipped draft; complete history alone does not activate it.
3. Improve independent news/macro contribution, Elliott/psychology support,
   dedicated forward evaluation, browser QA and upload race resilience.
4. Keep this checkpoint and HANDOVER current with evidence at every phase.

## Continuing constraints

EUR 0; no paid services or trial activation. Bitget BTCUSDT USDT-FUTURES in USDT is
the primary reference; USD spot comparisons stay separate. Missing values stay
unavailable rather than becoming zero/neutral. Only appropriate closed candles
confirm levels. Preserve original observations and versions, including older
four-route internal records. General market context only; no personal trading
positions or orders. Existing NAS tasks are documented in HANDOVER; do not
recreate them based on an incomplete new chat.

Monitor schedules must be checked through their actual service. As read on
24 October, psychology was scheduled for 08:00 from 25 October while an older
archive paragraph still said 12:00. HANDOVER records that discrepancy without
silently changing a schedule. Similar dated statements should never be treated
as guaranteed live configuration.

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
