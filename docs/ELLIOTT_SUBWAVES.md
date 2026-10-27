# Anchored one-level subdivision validator — proposed v1

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
