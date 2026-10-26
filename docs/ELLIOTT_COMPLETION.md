# Endpoint structure and linked lower evidence — proposed v1

This implements price evidence from the accepted completion checklist. It does
not produce an Elliott count, nested 5-3-5-3-5 certification, preferred valid
count, new-wave declaration or calibrated probabilities. Standard-impulse
candidates remain independently checked; current stored candidates are invalid.

## Anchor and source scope

Each available native timeframe starts from its latest strict two-left/two-right
confirmed pivot. Pivot recognition requires the second following candle to close.
The endpoint is a price reference, not an assertion that a wave ended there.
The opposing swing is selected from the pivot sequence available at endpoint
recognition, rather than moved to make subsequent prices pass. A versioned
function can also assess an explicitly fixed earlier endpoint.

Only aligned, contiguous, valid closed OHLCV candles through the requested as_of
are used. Future/open candles are excluded. Missing/duplicate candles, an outside
candle with unknown high/low pivot ordering or an unavailable opposing swing
prevent assessment. No missing field becomes neutral or zero. Stored history
conflicts still block the affected parent entirely.

The lower timeframe resolves the SAME parent's extreme inside its native anchor
candle. It requires full child coverage, exact extreme agreement and exactly one
matching child candle. Duplicate touches, missing bars, a non-pivot lower extreme
or unavailable parent remain unresolved. It does not attach an unrelated latest
lower pivot. A lower source scale is not automatically a specific wave degree.

## Observable stages and chosen experimental rules

1. Pivot known: no opposite-direction closed swing break yet.
2. Swing broken: a closed candle passes the fixed opposing swing, once the
   anchor and that swing were known. Wicks alone do not meet this condition.
3. Pullback held: after the break, the first confirmed reversal-leg pivot is
   followed by a confirmed pullback. A strict lower high / higher low is required
   relative to the old endpoint. Equal touches remain unresolved at this stage.
4. Continuation: a later candle, opening after pullback recognition, closes beyond
   that first reversal leg. Earlier breaches are not reused as follow-through.
5. Endpoint extended: ANY later closed candle's wick exceeds the old endpoint.
   This overrides reversal stages for that fixed endpoint. When both sides are
   crossed inside one candle, no intrabar ordering is inferred.

These states are deterministic conditions to evaluate, not calibrated success
rates or universal wave-ending rules. Full required pattern/subdivision evidence
is still absent, so wave_completion remains unproven even at stage 4. Multiple
interpretations can remain valid. A daily/hourly reversal does not certify a
weekly endpoint. Every event records when its evidence became available.

## Supporting data and remaining work

The separate current 4H momentum/spot/futures panel remains available with its own
strict window/freshness/coverage checks. It is NOT projected onto historical daily
or weekly pivots, counted as extra independent price votes or used to fabricate
percentages. This first price-state layer does not yet join event-aligned historic
flow features. Pattern/subdivision generation and validation, persistent frozen
hypotheses/outcomes, calibrated evaluation and probability estimates remain open.

Own-timeframe display selects the latest known pivot anew each build; lower
analysis holds that selected parent pivot fixed within the build. These are not
persistent scenario identities or a guarantee that an earlier active count is
unchanged forever. Existing original measurements/reports are not rewritten.
As-of tests exclude future pivot confirmation and later candle contents.

The weekly source conflict remains rejected. On the existing October 26 archive,
the daily high 84870 is only a pivot-stage endpoint, while the lower 4H check of
that exact high is further along at pullback-held. This is structural price
evidence, not validation of either old six-pivot impulse or a finished week wave.

Validation includes mirrored bullish/bearish progression, wick vs close,
equal retest, time leakage, gaps/duplicates, outside candles, child anchor identity,
extreme conflicts/ties, blocked parent and no mutation of original rows. Existing
full release generation and asset gate must pass on Python 3.9.14 and 3.11.
Public and genuine phone visual acceptance follow reviewed merge/publication.
