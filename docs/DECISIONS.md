# Accepted project decisions

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

Open PR #65 adds a guarded producer and separately archived draft review. The
2021 peak reference and post_peak phase are explicit review proposals, not newly
accepted automatic cycle classifications. The default remains draft/current v4
anchors; activation requires a separate reviewed configuration change. Local
archive validation must be labeled distinctly from network retrieval.
