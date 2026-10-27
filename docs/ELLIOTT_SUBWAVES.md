# Anchored one-level subdivision validator — proposed v1

## Forming-prefix extension — 27 October 2026

New `assess_prefix` model `elliott_anchored_prefix_subdivision_v1` uses the same
source/anchor/lower-outline checks for the ONE TO FOUR already formed legs of
a current as-of standard-impulse prefix. The completed six-pivot `assess` contract
and model remain unchanged. Visual bundle version is now
`elliott_visual_anchored_prefix_v7`.

Rebuild the as-of prefix inventory and require the supplied ID, exact pivot
anchors and direction to match. Recompute the prefix rules, including its ongoing
wick constraints; a caller cannot turn an invalid parent into a passing one by
changing its status. Obsolete, forged or future anchors stay unavailable. Then
validate all parent pivot recognition and exact covered parent/child OHLC/BTC
volume before mapping each formed leg to unique native child extremes. All
confirmed child pivots between those fixed anchors remain in the selection.

Formed odd legs use a five-leg standard-impulse price outline; even legs the
existing restricted three-leg zigzag outline. Source gaps/conflicts, repeated
extremes, extra pivots and unsupported corrections retain their existing blocked,
unavailable or unresolved meanings. Do not treat the latest unrelated lower
hypothesis as proof of a higher leg. The display shows the actual lower pivot
rows, recognition times and tests inside each forming proposal's disclosure.

The next ONGOING parent leg has no confirmed end anchor:it is explicitly NOT
subdivided by this extension. `formed_legs`, `ongoing_leg` and
`ongoing_leg_status=unconfirmed_parent_endpoint_not_tested` keep that limit clear.
Compatibility of all n formed legs does not certify a full five-leg wave, deeper
internal subdivisions, parent degree, preferred scenario or probability. The
higher/lower labels describe source scales, not a proved Elliott degree. Current
4H flow/momentum remains separately scoped; no historical flow is backfilled.

Validation:508 Python tests,6 Node tests, full offline dashboard/actual source-SVG
gate (42 charts) and diff check passed locally. Seven new test methods cover
one-to-four formed legs in both directions, exact shared prices, no mutation,
forged/stale/future anchors, rechecked invalid parents, missing/conflicting/duplicate
child sources, ambiguous child extremes, future/open exclusion and source-blocked
UI. Existing completed-outline/endpoint tests stay green.

On the PR88 corrected archive at11:30UTC/12:30CET, each usable week/day/4H parent
has an unresolved one-leg prefix;the mapped child span contains1,3,1 legs,
respectively, rather than the required5. They remain unresolved. Hourly proposals
are invalid and no finer native source is available. This is honest source-linked
evidence, not an assertion of a valid current count. Lower cached history is
historical at that later cut-off;the source scopes remain visible. PR88 is still
open; scheduled audit and live correction acceptance still wait for merge.

Scope: existing, preselected standard-impulse price candidates. This adds a
validator, not a generator of a new current count or a preferred interpretation.
No probabilities or full wave certification are produced. Model output keeps
wave_certification=unproven even when all five lower price outlines fit.

## Source and anchor contract

- Recompute the parent's existing hard price/wick rules; an invalid parent is
  blocked before looking for attractive children. Candidate selection is unchanged.
- Recheck the parent's strict pivots at their own recognition times and as_of.
- Use aligned, contiguous closed native child candles. Verify all covered parent
  OHLC/BTC-volume groups against their children; missing/conflicting groups fail.
- Resolve each higher anchor to ONE exact lower extreme inside its original
  native parent candle. Ambiguous repeated touches or a non-pivot lower extreme
  remain unresolved; no nearest-price tolerance or unrelated pivot substitution.
- Select ALL lower confirmed pivots from mapped start to mapped end, reconstructed
  when that lower end first became knowable. Do not skip extra pivots or search
  subsets for a fitting count. More/fewer pivots mean the degree is unresolved.

The source scale does not establish wave degree automatically. The higher
candidate must already have a defensible price outline; lower pattern matches
cannot fix its violations. Weekly source-conflict gating stays unchanged.

## Limited pattern families

Higher legs 1/3/5 are checked for a five-leg STANDARD-impulse outline, including
wave-2 origin, wave-3 progress/length and wave-4 overlap checks on intervening
wicks. Higher legs 2/4 are checked for one restricted non-truncated single zigzag
outline: three alternating legs, B strictly inside A including its wicks, C beyond
A. An unsupported zigzag outline does NOT invalidate every corrective pattern.
Flats, triangles, diagonals, combinations and other/truncated corrections are not
implemented. No rule is relaxed to rescue an unavailable family.

Primary framework definitions reviewed:
- https://www.elliottwave.com/waveopedia/impulse/
- https://www.elliottwave.com/waveopedia/zigzags/

These distinguish an impulse's 5-3-5-3-5 and a zigzag's internal 5-3-5. Wave 1/5
may have other motive families; this implementation restricts its tested family
to standard impulses. Framework descriptions are not empirical proof of BTC
predictive usefulness. Existing strict overlap policy remains unchanged.

The children are themselves price outlines, not recursively certified waves.
Their deeper internal requirements remain explicitly not testable at this layer.
Even compatible_outlines for all five higher legs is therefore not a completed
Elliott count, proof of current wave position or calibrated 5/5 success rate.

## Dashboard and current data

The historical candidate's rules disclosure includes the lower-scale outcome,
observed/required leg counts, actual mapped pivot prices/timestamps and checks.
Invalid higher candidates show blocked; unsupported or ambiguous cases show
unresolved. Existing charts, endpoint/retest stages and current 4H flow panel
retain their independent scopes. No historical CVD is projected onto old pivots.
Visual model: elliott_visual_subdivision_evidence_v5.

Current daily/4H candidates remain invalid, so the live-data preview correctly
blocks their subdivisions. 1H has no finer native source in this view; no missing
child is fabricated. New active candidate generation, further pattern families,
recursive validation, persistent fixed scenario outcomes and calibrated
probabilities remain open work.

Validation fixtures include fully anchored 5-3-5-3-5 outlines in both directions,
a six-point lower impulse with a genuine overlap violation, seven lower legs that
are NOT thinned to five, ambiguous repeated anchors, source conflicts/gaps,
future confirmation and open-candle exclusion. Source rows/candidates are not
mutated. Release CI includes Python 3.9.14/3.11 and actual Pages asset staging.
