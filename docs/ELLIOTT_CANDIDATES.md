# Forming standard-impulse inventory

Model `elliott_forming_impulse_inventory_v1` adds a bounded hypothesis inventory
beside the existing historical completed-outline candidates. It does not choose
a preferred Elliott count or replace either endpoint or momentum evidence.

## Selection and checks

At each as-of time, validate contiguous native closed OHLCV and select every
suffix of 2, 3, 4 and 5 confirmed pivots ending at the latest confirmed pivot.
Use the existing strict two-left/two-right pivot extractor, including its
same-kind extreme consolidation and exclusion of outside candles with unknown
extremum order. This is one pivot scale, not exhaustive enumeration of degrees
or possible wave families. No intermediate selected pivots are removed to pass
rules; neither direction is forced into a preferred slot. Invalid hypotheses
stay in the inventory.

The assumed first leg determines the hypothesized impulse direction. The next
unconfirmed leg can have the opposite direction: an upward impulse after one
pivot leg proposes a downward second leg. Labels always remain questions.

Test formed directions, wave-2 origin and wave-4 overlap with every intervening
wick, and the formed wave-3 end against wave 1. For every fixed anchor, reject a
later wick beyond that anchor during its following formed leg; apply the same
condition to the last anchor during the ongoing leg. For a proposed ongoing
second/fourth leg, check origin/overlap immediately. During a proposed fifth
leg, reject the fixed variant if wave 1 and the already observed fifth length
are both longer than wave 3. Unformed length rules are not passed by default.
The ongoing extreme is a closed-candle observation, not a confirmed pivot or
target; no unknown tick ordering is invented. Touches of strict origin/overlap
boundaries fail this conservative standard-impulse policy.

A failed fixed variant may need different anchors or another family; rejection
is not a universal rejection of a bullish/bearish direction. Passing price rules
does not establish that the first assumed leg really is Elliott wave 1. Internal
subdivisions, degree, parent linkage, alternate corrections/diagonals, event-time
volume and momentum remain unproven. These prefixes do not inherit PR87's
completed-parent subdivision verdict; those inputs have different contracts.
The primary framework reference is [Waveopedia: Impulse](https://www.elliottwave.com/waveopedia/impulse/).
The strict futures overlap policy is inherited from this project; no exception
was added based on the framework's discussion of leveraged markets.

## Timing, identity and presentation

Open/future candles cannot affect output. Every anchor shows its pivot-candle
opening and recognition time. `closed_through` and a separate scope distinguish
the latest complete source window from an older contiguous prefix. Dashboard
source conflicts block the affected scale before inventory construction; an
old prefix is explicitly historical, not silently presented as current.

IDs hash model, timeframe, family and all fixed pivot anchors/prices/recognition
times. New following candles preserve an ID while anchors are unchanged; a
source revision or replacement pivot yields a different ID. These are repeatable
snapshot identities, not an immutable forecast/outcome ledger. No new snapshot
archive or historical outcomes are written by this read-only module.

Each proposal has an expandable anchor/rule disclosure and a chart zoomed from
its own origin through the last closed candle. Only confirmed pivot points are
numbered as hypotheses. The unconfirmed extreme is separately described. Both
`preferred_id` and `current_wave` remain null; certification is unproven and all
probabilities null. Existing NAS records, scores and historical proposals stay
unchanged. No fixed probability can be derived by counting these four proposals.

## Validation and remaining work

Tests cover all fixed suffixes regardless of rule result, mirrored directions,
ongoing wick violations, fixed endpoint extension, a shortest-third violation
while the fifth is still forming, unformed rule state, open/future exclusion,
stable IDs, malformed/gapped/duplicate data, stale scope and source-blocked UI.
Combined with PR87: 490 Python tests, six Node tests and actual offline dashboard
asset comparison pass locally. Current main archive at 81702449f631b26374871ca4eedd4d20f36b3f79
has source conflicts for 1W/1D/4H and a historical 1H prefix: only that prefix
produces four proposals (three invalid, one unresolved). It is not a live count.

Next: merge/release acceptance, then link eligible forming prefixes to exact
parent anchors and lower substructures, expand supported pattern families, and
create frozen event/outcome histories before out-of-time probability calibration.
No extra NAS action is needed. Phone rendering/live deployment not yet accepted.
