# BTC Monitor — current scope and open work

## Current development — experimental frozen Elliott ledger, 27 October 2026

A separate PR proposes opt-in observation and first-invalidation primitives in
scripts/elliott_outcome_ledger.py; see ELLIOTT_OUTCOME_LEDGER.md. Fixed original
candles and inventory are checked against later data and remain immutable; gaps,
changes to old inputs and caller-declared conflict are rejected. This is NOT a
running archive, backfill, valid success rate, calibrated probability, deployed
change or a trustworthy source gate by itself. It needs a separate reviewed
integration with actual timestamps, validated source eligibility, revision policy,
retention and concurrency. No schedule, market data or NAS change. Local validation: 513 Python tests,
six Node tests and offline dashboard asset gate (30 charts) passed. Required
Python 3.9/3.11 CI and post-merge deployment acceptance remain pending.

Next: after review/merge and executable CI, implement the source-validated live
runner and availability capture in a new PR. Further independent Elliott family
work can start now. The 4H source discrepancy remains blocked pending fresh exact
source evidence, separately documented in ELLIOTT_20261027_SOURCE_CONFLICT.md.


## Current checkpoint — PR89 merged; 4H source conflict investigated, 27 October 2026

PR #89 merged as 67a2bcda0e69679a5ef1ee423006521219a6248f. Release CI
40554888188 succeeded at final PR head ed99c9ee43e6af2166c1191e30e5cadc05bb5435;
exact-merge Pages 40555066975 succeeded. This establishes publication, not a
manual mobile or current expanded-flat visual acceptance.

The 12:00–16:00 UTC native 4H/1H conflict occurred in the original 16:02 UTC
provider responses and the 4H close plus final 1H close were reproduced by the
revision audit seconds later. Its unchanged tail verdict is not cross-timeframe
validation. The history workflow failed on the source conflict but preserved
checkpoints and its audit artifact. The cause and correct final values are unknown.
An attempted fresh Bitget request in this environment was unavailable. Detailed
source evidence, audit scope, cutoff distinction and next decision are documented
in [ELLIOTT_20261027_SOURCE_CONFLICT.md](ELLIOTT_20261027_SOURCE_CONFLICT.md).
No data, rules, NAS runtime or schedules were changed. This documentation is
proposed in PR #90 (https://github.com/Cravendor/btc-monitor/pull/90); do not call the conflict repaired.

Next: inspect a fresh exact-window native 4H and four hourly responses, retain raw
values and timestamps and review a separate source correction only if supported.
The existing workflow may produce new evidence; later unchanged audit tails alone
do not cover the old interval. Independent work may proceed now on frozen
outcome histories or other correction families. No manual NAS task is required.

## Current development — expanded-flat endpoint geometry, 27 October 2026

PR #89 (https://github.com/Cravendor/btc-monitor/pull/89) proposes a narrowly scoped expanded-flat endpoint check for
confirmed lower pivots. Both directions require B strictly beyond the start of A
and C strictly beyond its end. Interior 3-3-5 remains unverified; a matching
outline is not a certified wave, proven degree or probability. Other flat types
remain unsupported. The existing source, anchor and parent validity gates remain
unchanged. No NAS, historical input, schedule or original report is changed.
Offline validation: 510 Python tests and six Node tests passed; actual asset
quality gate passed with 30 charts. At the 17:51 UTC build, the input reported
one 4H/1H conflict for the 12:00 UTC candle (4H close 80459.3 vs hourly
aggregate 80523.4; base volume 6965.3543 vs 7626.8427 BTC) and one missing 1H
candle at 16:00 UTC. These are recorded source states, not proof of cause or
collector failure; the affected 4H source remains blocked. Recheck original
source evidence before any source repair. Required Python 3.9/3.11 CI and
exact-merge live acceptance remain pending.
See ELLIOTT_SUBWAVES.md for the contract and limitations. This branch is not yet
merged or deployed. Review and merge follow successful required CI; afterward
verify exact-merge Pages. Frozen outcome histories and further families/degree
validation can proceed independently; no new manual NAS task is required.


## Current checkpoint — PR88 deployed and accepted, 27 October 2026

This supersedes all PR88 open/pending-publication checkpoints below. User merged
PR88 as7b7262bf8fef4d83e45494b370d86a34de4623d1 at11:52:31UTC/12:52:31CET.
Exact-merge Pages40499412625 succeeded. First existing history workflow
40499413684 also succeeded:collection/checkpoint and revision-evidence artifact
steps both green. Post-history Pages40499452388 at169777db1202c4de4e9f9236110fd142e0a0f753
succeeded. No further waiting for this initial deployment or normal audit run.

Actually read the new committed automatic audit:
data/history/source-revision-audits/20261027T115245Z-54fc7da1e52921eefdecd4604d6e82b8901a3db960116af855505efc4c057f10.json.
At11:52:45UTC/12:52:45CET all four tested windows were unchanged and their cached
tails current for the selection cut-off. All four cache-file SHA256 values match
the audit. Native coverage at that cut-off:69 weeks,483 days,2900 four-hour and
11603 hourly candles;all complete,zero cross-timeframe source mismatches.
Closed bounds:weekOct26 00UTC,dayOct27 00UTC,4HOct27 08UTC,1HOct27 11UTC.
These are timestamped results,not a guarantee after new intervals close.
The bitget-source-revision-audits artifact is present,not expired,id12731224359,
1881 compressed bytes. Normal execution/upload accepted;an actual failed-push
artifact fallback was not induced or claimed.

Actual public Chrome acceptance at https://cravendor.github.io/btc-monitor/:
all1W/1D/4H/1H disclosures open and source charts available. Weekly corrected
close80119.2 displays;daily80117.1,4H79784.0,hourly79942.5 at their stated bounds.
Expanded weekly forming proposal shows the same-anchor daily subdivision table:
1 observed lower leg versus5 required,unresolved. Ongoing higher leg2? explicitly
has no confirmed endpoint and is not subdivided. Desktop chart/table screenshot
inspected and readable;no iPhone acceptance claimed. Current wave/degree and
probabilities remain unproven,even though source/deployment acceptance is closed.

No executable changes or redundant full test suite in this acceptance task.
Prior508 Python/6 Node/two-version release validation remains recorded below;
this task verifies the new merge,actual publication,normal workflow/audit/artifact
and live controls. No extra manual collection,operational repair or user action
required. Future development must use a NEW separate PR;do not reopen/extend PR88.
Do not repeat this completed acceptance without a relevant change or incident.
User asks for efficient progress,immediate direct result links and no repeated
status loops. Next agent work can start immediately:additional corrective pattern
families and degree validation,then frozen outcome histories before probability
calibration. No need to wait for another routine observation to start that work.

### Concurrent main update reconciled — 27 October 2026

PR88 conflicted with the advancing main branch before new CI could run. Prepared and committed a normal merge of
main8d7637b5bfd207b4b7776a42985d63e16e42b041 into PR88, preserving both parents.
Only3 overlapping candle differences exist:the same already-audited native
revisions. Keep those reviewed values and all original evidence. Preserve every
other candle and all page provenance from both sides, including5 newer main1H
candles;hourly cache now11602 rows, other counts unchanged. All newly published
snapshots/reports/receipts and signal/context histories from main are preserved.

Recomputed strict review has zero source mismatches;4H/hourly coverage is still
partial (first missing Oct27 04UTC/10UTC), explicitly not current completeness.
No forced push, source-rule relaxation or unrelated data deletion. Full merged input passed508 Python tests,6 Node tests and the exact42-chart
asset gate;both required release CI versions also passed at the commit below.

## Current checkpoint — formed-prefix lower linkage prepared, 27 October 2026

Authoritative current resume point; supersedes older awaiting-next-development
and validation metadata below. PR88 remains OPEN, not merged or deployed at this
check. Extend that same PR with explicit shared-anchor lower-outline evidence for
formed prefixes. Visual model elliott_visual_anchored_prefix_v7. Contract and
limitations are in docs/ELLIOTT_SUBWAVES.md (forming-prefix extension).

New assess_prefix rebuilds the exact as-of prefix inventory, verifies ID/anchors/
direction and recomputes all prefix rules before accepting it. Invalid parents
cannot be rescued. Existing strict source-group comparison, unique native lower
extreme mapping and ALL lower pivots between shared anchors now apply to one-to-
four FORMED higher legs. Odd/even legs use the existing limited impulse/zigzag
outlines. The next ongoing parent leg has no confirmed end anchor and is NOT
subdivided. No full nested count, wave degree, preferred scenario or probability
is certified. Completed-outline validator semantics/model remain unchanged.

Each forming disclosure now shows its lower pivot/rule evidence when available;
1H has no finer source and conflicts stay blocked. Actual PR88 archive at11:30UTC/
12:30CET:week/day/4H unresolved one-leg prefixes have1/3/1 mapped lower legs,
respectively, rather than required5;no passing interpretation invented. Lower
cached source remains historical at that later cut-off;no fresh data implied.
Current 4H flow/momentum stays separate;no historical delta or volume backcast.

508 Python tests,6 Node tests,diff and full OFFLINE dashboard/source-SVG gate
passed (42 charts). Seven new tests cover exact one-to-four leg linkage in both
directions, invalid/forged/obsolete/future parents, source gaps/conflicts, ambiguous
extremes, future exclusion, no mutation and UI boundaries. Merged executable/input commit 7a99090dc54201ff987ebfdcb61c51eb25ded966 passed required release CI:
Python3.9.14 check122169677364 and Python3.11 check122169676929, including actual
dashboard staging and asset comparison. This documentation update records those results.

The earlier three-candle source correction and bounded automatic audit remain
part of PR88. They are NOT deployed or scheduled-audit-accepted yet. No new
source-cache edits, original report/snapshot revisions, extra task or runtime
change in this increment. Review/merge after NEW CI passes can start immediately;
public chart/revision checks wait for merge, exact-commit Pages and first existing
history workflow. Independent work:additional corrective families and explicit
outcome/availability histories for later calibration;no extra manual action needed.

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
SVG gate pass (42 charts). Executable commit 58ec26cebd83f0ffc19d5b6b5442fe052eeb3af8 passed required release CI:
Python3.9.14 check122077549000 and Python3.11 check122077549384, including actual
dashboard staging/assets. The following metadata-only commit records those results. Public
PR88 correction acceptance still waits for user merge and successful exact-commit
Pages. Then inspect first existing history workflow's new audit/result/artifact.
No extra manual run or task is needed. Independent work can begin now:exact
parent-anchor linkage for forming prefixes and supported pattern families;
frozen outcomes before probability calibration. No certified current count.

### PR87 live acceptance and reviewed native-candle correction — 27 October 2026
PR88: https://github.com/Cravendor/btc-monitor/pull/88 — open, mergeable, not deployed.
Executable/data commit 27117179d1270e711848f83c1274270f78b60f2b passed both release CI versions:
Python3.9.14 check122055100803 and Python3.11 check122055100540. Public acceptance
still waits for reviewed merge and successful exact-commit Pages.


Current resume checkpoint; supersedes PR87 awaiting-merge/deploy and permanent
weekly-conflict wording below. PR87 merged as672c0ddedbaa851e13c5e40b0d499b0e5d6bb1be.
Exact-merge Pages40454980380 and final-head release CI40454538891 succeeded.
Actual public Chrome1H disclosure/table/anchors/chart verified:three invalid
proposals and one unresolved downward two-leg prefix; own focused chart/1?/2?
labels render, fixed ID5eaf43b99996fa5cf803c184, history throughOct27 00UTC.
Desktop screenshot readable; no phone acceptance claimed. This accepts PR87's
published feature, not a current/certified Elliott count or probability.

New source investigation completed with four fresh public native Bitget queries
and three exact original-query replays. All now reconcile; source changed after
the earlier observations. WeekOct19 close now80119.2/base217958.5411 agrees with
seven daily rows; dailyOct26 and4HOct26 20UTC also revised. Exact raw Decimal
comparison:48 four-hour groups,8 daily groups,1 weekly group have zero OHLC/base/
quote mismatches. Same-window broad vs original queries return identical revised
rows. Unknown internal cause; no tolerance relaxation or derived-week replacement.
Evidence/procedure: docs/ELLIOTT_SOURCE_AUDIT.md and new preserved original-response
file data/history/source-audits/20261027T052431Z-week-day-4h-1h.json.

Prepared reviewed cache correction:exactly3 existing native rows replaced, full
prior rows/pages/hashes preserved in audit, provenance appended to current files.
All other old candles unchanged; no original NAS snapshot/report rewritten.
Existing bounded collector then succeeds adding1 four-hour plus5 hourly candles;
full strict source/hash/coverage checks pass at05:30UTC/06:30CET:1W69,1D483,
4H2899,1H11597; no gaps or cross-timeframe mismatches. Source views only; past
as-observed data must not be backfilled with corrected values for calibration.
This is a one-off reviewed repair; automatic revision detection/activation is NOT
implemented. Future source conflicts still fail closed.

Local490 Python tests,6 Node tests,diff and full OFFLINE dashboard/actualSVG gate
pass (42 charts). History-data PR changes now trigger the two-version release
workflow by including data/history/** in its path filter. All four timeframes
available in preview; no preferred/current count or calibrated percentages.
At cut-off1W/1D/4H only the one-leg prefix remains unresolved; all1H prefixes
invalid. Public chart/source acceptance of this repair waits for reviewed merge
and successful exact-commit Pages; PR/CI metadata follows publication.

Next:user can review the repair PR after green CI; agent verifies live all-four-
scale availability after merge/Pages. Independent immediate work:bounded source-
revision audit policy and same-anchor parent/substructure linkage for prefixes.
No extra NAS task/log/run or old repair command is needed. Continuous recorder
and normal publisher recovery stay closed and protected.


## Open implementation work

- Review and merge the native-candle correction after green release CI, then verify all four chart scales on the public deployment.
- Define a bounded source-revision audit and activation policy preserving original observations and later revisions separately.
- Link forming prefixes to the same higher anchors and validate supported lower substructures; expand alternative pattern families without forcing opposite directions.
- Preserve independent evidence groups for structure, spot/futures flow and momentum. Correlated price indicators are not independent probability votes.
- Build frozen event/outcome histories and out-of-time evaluation before calibrated scenario percentages. No preferred current Elliott count is certified.
- Complete phone rendering acceptance; desktop inspection does not establish iPhone behavior.

Budget remains EUR 0, using public data and existing public repository workflows. Original reports and measurements must remain immutable. The existing recorder and normal publisher require no extra user action for this correction.

This status file has been consolidated to public project progress. Previous status entries remain in Git history. See [HANDOVER.md](HANDOVER.md), [DECISIONS.md](DECISIONS.md), [ELLIOTT_SOURCE_AUDIT.md](ELLIOTT_SOURCE_AUDIT.md), [ELLIOTT_CANDIDATES.md](ELLIOTT_CANDIDATES.md) and [ELLIOTT_SUBWAVES.md](ELLIOTT_SUBWAVES.md) for existing project contracts and evidence.
