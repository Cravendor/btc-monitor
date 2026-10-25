# Elliott visual checkpoint — 25 October 2026

The homepage now draws closed native weekly, daily, 4H and 1H candles with the
two most recent six-pivot standard-impulse candidates, selected independently of
rule outcomes. Bull and bear are shown separately; invalid candidates remain
explicitly invalid. Missing degrees remain unavailable. These candidates do not
establish the current wave, internal 5-3-5-3-5 or a nested top-down count.

Charts preserve every intermediate candle/wick, mark the latest closed candle,
and distinguish a fresh ticker from historical source plots. Old observations
remain visibly historical and do not generate a current ticker. Pivot candle
openings are UTC, not exact extremum tick times. The source window is limited;
its highest high is not labeled a lifetime ATH.

Each degree has a price-ordered zone table and shaded bands. Width is fixed at
±0.15 ATR(14) around the first confirmed pivot. Repeated independent pivot events
are counted; consecutive candle touches are not separate evidence. This is an
uncalibrated description of observed reactions, not a prediction of strong
support or rejection probability. Local zones do not invalidate a higher degree.
Fib context is calculated from the final candidate price leg, stays distinct
from measured support, and does not rescue an invalid count.

Temporal containment in a parent candidate leg is exposed for inspection only;
it does not prove subwave nesting. Full count and named corrective-family
analysis remain an interpretive task requiring more evidence. No projected wave
path or current wave is invented to fill an empty card.

Quality rebuilds source availability and requires the visual panel and exact
expected chart count before Pages uploads. Browser-side freshness updates the
historical warning. No sources, schedules, scores, original records or NAS
runtime are changed.

Validation: 419 Python tests and 5 Node tests; homepage generation with all four
degrees and eight charts; weekly SVG rendered and visually inspected. Full
browser/mobile interaction was not verified (browser executable unavailable).
CI, merge, Pages deployment and fresh-source behavior remain separate checks.


## Longer history adapter — 25 October 2026

The accompanying [long-history change](ELLIOTT_HISTORY.md) replaces snapshot-only
chart inputs with independently checked archives from July 2025. The previous
36-week/89-day visual limit is superseded by that adapter; the provisional
candidate-count limitations above remain. Publication/activation are separate
from the local implementation and source retrieval evidence.
