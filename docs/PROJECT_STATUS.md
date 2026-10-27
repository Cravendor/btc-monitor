# BTC Monitor — current scope and open work

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
