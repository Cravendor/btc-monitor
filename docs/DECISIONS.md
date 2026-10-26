# Accepted project decisions

## Multi-source momentum switch required — 26 October 2026

User clarification: daily candles alone are insufficient for the stronger
wave-end/new-wave confirmation label. Explicitly incorporate spot AND futures
volume, validated buy/sell deltas, momentum changes and other relevant evidence.
Detect the CHANGE through time, not just a static bullish indicator count.
A bearish indicator becoming less negative is weakening bearish momentum,
not yet an established bullish switch.

Proposed evidence groups: (1) structural break, higher/lower swing and retest
at stated degree; (2) price momentum group RSI/MACD/ROC (correlated derivatives,
one group rather than three independent votes); (3) separately labeled spot
and futures relative candle volume and same-window provider-side deltas;
(4) derivatives positioning context: OI in BTC/price-adjusted notional, funding,
basis and liquidation context where genuinely available; (5) optional independent
demand/liquidity context such as ETF flows and premium with correct horizon.
Volume growth alone has no buy/sell direction, rising OI alone has no directional
sign, positive funding alone is not bullish confirmation. Futures-led moves may
reflect leverage/short covering; classify using joint evidence, not an OI slogan.
Our CVD uses provider buy/sell convention, not independently proved taker flow.
OBV/CMF are candle-volume proxies and cannot substitute for actual trade delta.

Record synchronized comparable closed windows, prior/current values, support,
counterevidence, missing/stale inputs and degree-specific invalidation. Show
price-only/pivot confirmation separately from multi-source momentum support.
Do not label the strongest multi-source state when mandatory spot or futures
evidence is missing; do not discard valid price observations either. Preserve
a separate data-coverage state. Independent consistent groups can strengthen
support; correlated indicator count cannot mechanically become a probability.
Temporal persistence/follow-through matters, with thresholds to be tested and
frozen before evaluation. Suggested UI states: bearish momentum, bearish
pressure easing, tentative bullish switch, supported bullish switch (mirror
for bearish), with explicit scope and contradictory evidence.

This extends the preceding completion/probability specification; it does not
claim this scoring/detection is implemented or calibrated. Actual local July
pivot evidence remains a price-structure fact, not retroactive flow confirmation.
Primary references checked: Fidelity technical indicator guide/OBV explanation,
Bitget classic historical funding docs. No new data collection, paid service,
NAS action, code or runtime tests. Next agent action can start immediately:
implement/test synchronized evidence states and feature availability inventory.
Numerical calibrated probabilities still wait for defined outcomes and proper
historical/out-of-time validation. UI/zoom/source-discrepancy work can continue
independently; no need to wait for NAS upload checks.


## Wave-completion evidence and scenario probabilities — 26 October 2026

User asks for researched criteria for the most likely wave termination/new wave,
and numerical scenario probabilities using all suitable available evidence.
This requests probability estimation, not fabricated percentages or permission
to relabel an arbitrary score as calibrated likelihood. Existing no-invented-
probabilities constraint remains. No probability model is implemented/validated.

Read actual current daily archive blob 00e28236282fe88a5b2eb43db103f31b7e55c240:
Bitget BTCUSDT USDT-FUTURES low 57770 on 2026-07-01 UTC; prior daily lows
58866 and 58160.1, next daily lows 59562.4 and 61223. Thus the archived low
meets existing strict two-left/two-right daily pivot criterion after the second
following candle closes (4 July 00:00 UTC). Subsequent stored high is 87373.
This verifies a historical daily pivot and subsequent rise, not automatically
a completed macro bear cycle or a specific weekly Elliott count. No snapshot
or current CVD may be backfilled into July observations.

Researched completion checklist to operationalize, with explicit degree:
(1) acceptable same-market source data, valid proposed pattern and actual
required subdivisions; impulse and corrective pattern endings are distinct;
(2) reversal through preselected opposing structural swing/channel using
closed candles for the defined confirmation condition;
(3) new directional substructure, pullback holding the candidate origin and
subsequent continuation; higher low alone is weaker than continuation;
(4) parent-degree condition/closed-candle follow-through, no hourly move alone
certifies weekly completion; (5) momentum divergence/volume/Fibonacci/orderflow
as supporting evidence, never sufficient proof or independent duplicate votes.
Hard intrabar rule violations still invalidate counts independently of closes.
These are proposed operational evidence stages, not universal guaranteed rules.

Probability target must specify degree, future horizon, immutable trigger/
invalidation levels and mutually exclusive outcome definition (including
neither/expired/unresolved; ambiguous same-candle ordering stays unresolved).
Different degrees may both realize sequentially; bull+bear are not automatically
complementary events. Fit/calibrate on point-in-time historical features, validate
on later untouched periods with gap/purge for overlapping label horizons, compare
base-rate forecasts and reliability curves/Brier/log-loss with sample counts
and uncertainty. Existing frozen scenario evaluator is descriptive and does not
provide calibrated Elliott probabilities. Macro effective samples may be few
despite many candles. Missing features stay missing, not zero; no price/RSI/
MACD/Fib double counting, future-confirmed pivots cannot be used before their
confirmation time. Separate historical price-only model from enhanced model
whose CVD/OI/news histories genuinely exist. No retroactive claims that we had
all these inputs in 2021/July. Interim support score, if implemented, must be
labeled uncalibrated and not displayed with a probability percent sign.

Primary framework sources read: Elliott Wave International Waveopedia,
Impulse, Channeling, Wave Personality, Extension (stock-market tendencies are
not automatically validated for BTC). Statistical references: scikit-learn
Probability calibration and TimeSeriesSplit docs. Framework descriptions are
not independent evidence of forecast profitability. Research/context only,
no runtime/code/data changes or new tests. Handover and decisions maintained.

Next agent action can start immediately: implement explicit completion-evidence
states and frozen evaluable scenario outcomes with provenance/tests, then assess
point-in-time training coverage before fitting probabilities. UI/zoom work is
independent. Numeric calibrated weekly chances must wait for sufficient valid
history, source reconciliation and out-of-time validation; no extra NAS action.


## Corrected Elliott dashboard intent — 26 October 2026

Latest user clarification REPLACES always showing a bull and bear chart for every
timeframe. Desired view: start with weekly context and the latest relevant
completed/active wave; show its tentative endpoint/completion evidence, then zoom
into its internal daily/4H/hour subdivisions. Use linked parent/child labels and
shared timestamps/price anchors, not unrelated latest-six-pivot counts. Provide
overview plus zoomed active-leg/detail views and zoom in/out. Do not claim the
current implementation already proves this nesting or current-wave identity.

Show a preferred conditional interpretation and a material valid alternate where
the endpoint/next structure is unresolved. Alternates need not always point in
opposite directions; distinct counts may share the same next direction. Do not
hide a still-valid alternate just because one directional move is confirmed.
If no defensible count exists or sources conflict, state unavailable, not a
fabricated next wave. Distinguish observed pivots, tentative count and confirmed
structural condition; a completed-looking pattern can extend or belong to a
different degree. Timeframe and wave degree are related but not identical.

User theory was checked against Elliott Wave International Waveopedia and
Extension: https://www.elliottwave.com/waveopedia/ and
https://www.elliottwave.com/waveopedia/extension/ . Treat as primary documentation
of the Elliott framework, not independent proof of predictive accuracy.
Higher structure constrains interpretation; lower subdivisions can provide
earlier reversal/completion evidence, but a low-timeframe reversal alone cannot
confirm a weekly endpoint. Define confirmation and invalidation per degree.
Closed-candle confirmation is distinct from intrabar hard-rule invalidation.
No invented probabilities, guaranteed direction or neutral for unavailable data.

PR #80 merge verified: 351d1df3a1550aa44af0f59e00c6302aa86531c7. Its small
conflict explanation is merged, not a complete redesign or a resolved source
discrepancy. New linked active-wave/zoom behavior is a requirement, not implemented.
Next agent work can begin immediately: specify/test linked wave-degree evidence
and active-leg chart views, investigate preserved week/day conflict separately;
no NAS wait. Weekly valid-count display must wait for acceptable source agreement.
Independent UI/zoom work need not wait for that source resolution.
Handover/status/decisions updated for this clarification. Validation: merged PR
metadata, current docs, primary framework sources; no code or new runtime tests.


## Next-step readiness and independent work — 26 October 2026

Standing user instruction: every completion still ends with **Volgende stap:**,
naming the actor and concrete action. Also state whether work can start NOW or
must WAIT for a check/execution/result, identify the actual dependency and what
evidence releases it. When waiting, explicitly name useful authorized work that
can start independently, or say none is currently identified. Continue such work
when appropriate; waiting for one result need not block unrelated project work.
Do not imply background execution or spawn parallel agents without authorization.

Current readiness: NAS new-runner ordinary publication acceptance is closed;
a future real writer race is observation only and does not block dashboard,
Elliott mobile or operational-status QA. Those checks can begin immediately.
No extra manual NAS run/log is needed now.


## Completion communication — 25 October 2026

Every task completion ends with **Volgende stap:**, the concrete next action
and who performs it. Record unresolved evidence plainly; do not imply work
continues in the background after the turn.

## Immediate handover maintenance — 25 October 2026

After every executed task, update HANDOVER.md and PROJECT_STATUS.md before
reporting completion; use the same change or immediately record an observed
external result. Record outcome/evidence, validation, PR/commit and the distinct
implemented/merged/deployed/observed states, blockers and next step. Update this
register for changed accepted decisions. This supersedes the weaker
“after a substantive phase” cadence. Do not publish private conversations or logs.


## Operational status decision — 25 October 2026

User requested a task-status page with coloured indicators. Show explicit text
alongside colour: green for recent execution evidence/running GitHub jobs, amber
for stale/queued/partial evidence, red for explicit failures/disabled workflows,
grey for unavailable/unconnected status. Do not infer a stopped continuous CVD
recorder from a failed or old NAS upload. No task-control buttons, paid service,
private runtime/log publication or duplicated DSM tasks are introduced.

Checkpoint: 24 October 2026. Latest user instructions override older proposals.
Implementation/activation status is in [HANDOVER.md](HANDOVER.md), not implied
by inclusion in this decision register.

| Decision | Accepted behavior | Superseded or excluded |
| --- | --- | --- |
| Cost and sources | EUR 0, public data, Bitget primary; clearly labeled secondary references | Paid APIs, trials, automatic subscriptions or trading credentials |
| Scope | General decision support at price levels for swing and longer horizons | Personal/model positions, automatic trades, fixed personal TP percentages |
| Competing hypotheses | Explicitly test bottom/absorption versus complacency/distribution with supporting and opposing evidence | Historical chart resemblance as proof; forced macro-bottom verdict |
| Missing data | Distinct unavailable/stale/partial status with source/time provenance | Null/error as zero or neutral; silently reuse an older green value |
| Public routes | Bull and bear together, each with five globally directional states and one combined interpretation | Four public scenario choices; route-dependent BUY meaning short versus long |
| 25 combinations | Five by five ordered mapping; conflicts stay explicit; some pairs may be unobserved/unreachable | 25 independent possibilities, invented probabilities or double-counted correlated evidence |
| Zone interpretation | Include tested zone, closed reaction, structure, confirmation/counterevidence and next attention point | A favorable meter automatically proving the next target or a retest |
| Timeline | Price-ordered path with origin, current-price marker and attention levels | Forecast arrival dates, observed position mistaken for past successful execution |
| Current anchors | User chose to retain available-history candidates for now, explicitly labeled limited | Silently replacing them with a lifetime ATH or an invented cycle low |
| Future macroanchor rule | Identify previous completed-cycle peak and current phase; see rule below | Fixed bear calendar year, latest 20 candles or every consecutive record tick as a completed cycle |
| Original history | Freeze original source/model/anchor/interpretation versions before future reactions; add versions for changes | Rewrite older forecasts with later knowledge or reconstruct old SHB where none existed |
| Quality | Engineering correctness AND observed forward usefulness; month/quarter/year review in one existing automation | Automatic threshold/weight/rule changes from small samples; claiming test success proves profitability |
| Infrastructure | Preserve continuous CVD recorder; periodic publisher and GitHub reserve are separate roles | Recreate a known DSM task or restart/delete the CVD journal to fix a snapshot upload |
| Report publication | New general market reports under current archive protocol; preserve actual original text | Publish private chats, personal finances/trades, credentials or internal task IDs |

## Latest macroanchor rule — supersedes calendar-year proposal

The previous completed cycle peak is an explicit, justified historical reference,
not necessarily the immediately preceding record high in the same rising cycle.
From complete same-market daily history after that reference, find the highest
measured high of the selected current cycle.

- Bear origin: that latest measured current-cycle high.
- During the explicitly selected advance phase, bull origin: lowest low strictly
  between the previous completed-cycle peak candle and latest high candle.
- In the explicitly selected post-peak phase, bull origin: running lowest low on
  candles strictly after the latest high. Higher or equal lows do not move the
  original anchor. A strictly lower low creates a new anchor version.
- A strictly higher high moves the bear origin and restarts the post-peak low
  interval. An equal high does not restart it. When no later closed low candle
  exists yet, report unavailable rather than infer intrabar event order.
- Same-candle peak/low order is unknown from daily OHLC. The implementation uses
  closed daily candles; it does not pretend to track live intraday extremes.
- Swing and position share these macroanchors when activated. Their reaction
  timeframes and volatility buffers may differ.
- A running low is a provisional departure point, not a confirmed final bottom.
  An identified high does not prove the current cycle is complete.

This rule is implemented as an opt-in contract in merged PR #62. It is NOT
activated automatically: prior peak/phase identification and a validated fresh,
complete multi-year source context remain necessary. The user accepted leaving
current observed-history anchors active until that is properly supported.

## Recent implementation milestones

| PR/commit | What it establishes | Does not establish |
| --- | --- | --- |
| #56–#59 | Swing/position scenarios, SHB history and selected price paths/origin display | Complete macrohistory or proved ATH/ATL |
| #60 | Two public routes, common five-state direction, 25 combinations, frozen original readings | Calibrated success rates or independent double confirmation |
| a64adc1 | One pending NAS measurement and both histories safely reconciled and pushed | A generic permanent fix for future writer races |
| #61 | Wider available-history high followed by later low, evidence and dates | Full cycle extremes; daily/week lows may still differ |
| #62 | Price-event macroanchor rule and guarded opt-in context | Automatic prior-cycle recognition, fresh history producer or active macroanchor mode |
| #63 (merged) | Complete 2021–2026 daily archive, independent resumable workflow, 361-test CI and initial workflow/Pages success | Next NAS source-reference storage or activation of #62 |

## Keep external state distinct

NAS tasks, GitHub workflows and ChatGPT automations are different systems. Keep
recorded configuration, actual executed run, original stored result and live
page evidence separate. Recheck external state before changes. Retain the
user's existing schedules and permission scope; this register does not itself
create an automation or authorize unrelated communications.


## Archive-context checkpoint

Merged PR #65 adds a guarded producer and separately archived draft review. The
2021 peak reference and post_peak phase are explicit review proposals, not newly
accepted automatic cycle classifications. The default remains draft/current v4
anchors; activation requires a separate reviewed configuration change. Local
archive validation must be labeled distinctly from network retrieval.

## Minimal execution receipts — 25 October 2026

User authorized connecting grey tasks where possible and including operational
failures in the existing Quality & Improvement review, without another scheduled
task. New receipts expose only task kind, actual times and completed/error. They
may be written after an actual no-alert check, without a user notification. No
private identifiers, log details or retrospective runs. Missing proof stays
unknown; runtime health and analysis quality remain separate. See TASK_EXECUTION.md.


## Mandatory report and dashboard quality gates — 25 October 2026

Latest user instruction requires a quality/recovery step in each existing
scheduled financial report/alert, plus per-update and existing periodic dashboard
checks. Monthly review alone is insufficient. Safe fixes may be prepared/tested
in separate PRs; no automatic merge, paid services, NAS restarts/journal edits or
new schedules. Reject unsupported claims while retaining explicitly usable
components; unavailable macro evidence is not a neutral verdict. Preserve original
reports and measurements. The live interval recovery and its remaining uncertainty
are recorded in CVD_RECONCILIATION.md; exact matching remains the coverage rule.
