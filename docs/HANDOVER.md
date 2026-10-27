# BTC monitor — agent handover

## Current checkpoint — automatic revision audit prepared, 27 October 2026

This checkpoint supersedes the older PR88 validation metadata below. PR88 is
still OPEN at the pre-publication check, not merged/deployed. Extend that same
PR with scripts/source_revision_audit.py,11 focused tests and integration in the
EXISTING history workflow. No new schedule or active-cache revision activation.
Read docs/SOURCE_REVISION_AUDIT.md for the exact contract and limitations.

Recheck the last2 validated cached closed candles for1W/1D/4H/1H, at most4 public
requests within75seconds. Retain both values, validated original row strings,
source/cache hashes, selection/observation times and current-vs-historical tail
scope. Unknown requester metadata and local filesystem locations never enter the
audit. Unavailable/invalid/budget-skipped checks cannot become unchanged. Exact
normalized comparison includes quote volume, without changing the chart gate.

Audits are immutable/content-addressed, staged completely and linked atomically
without overwrite. Existing cached files remain byte-identical. Current audit
is copied to one output JSON;workflow configured to preserve that single file
as an always-run30-day artifact even if Git publication fails. Actual workflow
execution/artifact acceptance remains pending;do not describe it as operational.

Live local public probe at07:56:15UTC/08:56:15CET onOct27:four selected windows
unchanged.1H cache tail is historical through05UTC (required07UTC), explicitly
not complete/current. Other tails current at this probe cut-off. Evidence in
new data/history/source-revision-audits/ timestamped file; no original snapshot,
report, current-cache candle, tolerance or operational runtime changed by auditor.
The proposed3-row source repair from earlier PR88 work remains separately scoped.

501 Python tests,6 Node tests, YAML parse,diff and full OFFLINE dashboard/source
SVG gate pass (42 charts). New code/CI commit metadata follows publication. Public
PR88 correction acceptance still waits for user merge and successful exact-commit
Pages. Then inspect first existing history workflow's new audit/result/artifact.
No extra manual run or task is needed. Independent work can begin now:exact
parent-anchor linkage for forming prefixes and supported pattern families;
frozen outcomes before probability calibration. No certified current count.

## Current checkpoint — 27 October 2026

PR88: https://github.com/Cravendor/btc-monitor/pull/88 — open, mergeable, not deployed.
Executable/data commit 27117179d1270e711848f83c1274270f78b60f2b passed both release CI versions:
Python3.9.14 check122055100803 and Python3.11 check122055100540. Public acceptance
still waits for reviewed merge and successful exact-commit Pages.

PR87 is merged as 672c0ddedbaa851e13c5e40b0d499b0e5d6bb1be. Exact-merge Pages
40454980380 and final-head release CI40454538891 succeeded. The public desktop
1H proposal table, fixed anchors and focused chart were actually inspected.
No iPhone acceptance or certified current Elliott count was established.

## Source repair prepared in PR88

Four public Bitget requests and three exact original-query replays now agree.
The provider revised the cached week opening October19, day opening October26
and four-hour candle opening October26 20UTC. Fresh raw Decimal comparison found
zero mismatches in all OHLC/base/quote fields for48 four-hour,8 daily and1 weekly
groups. All193 returned hourly probe rows match the preserved hourly source.
The provider's internal reason or revision timing remains unknown.

Exactly3 cached native rows are corrected in this proposed change. Their full
previous rows, original page metadata and archive hashes remain in the new audit;
all other old candles and original observations/reports remain unchanged. No
rounding relaxation or synthetic-week substitution was applied. The existing
bounded collector then resumed successfully:1 new four-hour and5 hourly candles.
At the recorded05:30UTC/06:30CET cut-off, all strict loaders and whole-history
source checks pass:69 weeks,483 days,2899 four-hour and11597 hourly candles.
This is coverage at that cut-off, not a guarantee of future/current completeness.

Preview shows all four scales and42 source-derived SVG charts. Weekly/day/4H
only have an unresolved one-leg prefix; hourly prefixes all invalid at that
cut-off. No preferred current wave or calibrated probabilities are established.
Automatic source-revision activation is still unimplemented:future conflicts
remain blocked, and corrected source values must not be backcast into forecasts.

Validation:490 Python tests,6 Node tests, exact changed/added-row preservation,
three original archive SHA256 checks and full offline dashboard/actual SVG
content-count gate passed. Both required CI versions passed at the commit above.
The release workflow path filter now includes data/history/** so historical-input
PRs also receive the full release checks. Live acceptance of this correction
waits for reviewed merge and successful Pages; phone acceptance remains open.

Evidence/contracts:
- [Source audit and correction](ELLIOTT_SOURCE_AUDIT.md)
- [Preserved API responses and previous rows](../data/history/source-audits/20261027T052431Z-week-day-4h-1h.json)
- [Forming hypotheses](ELLIOTT_CANDIDATES.md)
- [Anchored lower outlines](ELLIOTT_SUBWAVES.md)
- [Endpoint stages](ELLIOTT_COMPLETION.md)
- [Accepted decisions](DECISIONS.md)
- [Current status and remaining work](PROJECT_STATUS.md)

## Next step and independent work

User can review and merge PR88 after green final checks. Agent then verifies
successful exact-commit Pages and actual public week/day/4H charts. No additional
manual collection or old repair is required. Independent work can begin now:
bounded revision auditing/activation with original versions preserved; exact
higher-anchor linkage for forming prefixes; supported corrective families;
frozen event/outcome histories before out-of-time probability calibration.

## Standing constraints

Budget EUR0; public data and existing public repository workflows only. Missing,
error and stale data remain explicitly unavailable, never zero/neutral/success.
Preserve original measurements and dated reports. Treat structure, flow and
momentum as scoped evidence; correlated price indicators are not independent
probability votes. No private portfolio data or automatic trading. Protect the
existing continuous collector, database and publisher; a publication failure
alone does not establish that collection stopped. Never invent a schedule state
or request a duplicate operational task based on an old document.

Update this handover and PROJECT_STATUS after every task. End every completion
with Volgende stap, naming the actor, direct readiness versus actual waiting
dependency, and useful independent work. Code changes use reviewed PRs; user
merges. Required executable validation remains Python3.9.14 and3.11 plus Node
and actual dashboard asset checks. Do not claim merged/deployed/live-tested
interchangeably. Preserve other worktrees and local changes.

Historical versions remain in Git history. This file is consolidated to the
current public project state; no operational inventory or links to historical
operational metadata are included in this replacement.
