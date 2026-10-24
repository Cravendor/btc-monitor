# Archive to cycle-anchor context

`scripts/cycle_context.py` connects the validated multi-year Bitget daily archive
to the existing opt-in cycle-peak/running-low selector. No network requests or
historical-file writes happen during ordinary NAS collection. The collector
stores a compact `cycle_anchor_review` before freezing the original scenarios.
The dashboard shows this separately under **Controle macroankers**.

## Explicit selection and activation

`config/cycle_anchors.json` contains the reference peak, complete reference window,
prior/current cycle identifiers, phase and explanations. The shipped state is
`draft`: candidate anchors are calculated and stored for review, but there is no
`cycle_anchor_context` and the existing v4 route calculations are unchanged.
`disabled` skips selection. `active` supplies the validated original context to
the existing v5 selector for both horizons. Activation is a separate reviewed
configuration change; merging this adapter does not activate macroanchors.

The initial draft explicitly chooses the highest daily high within 2021 as the
previous completed-cycle reference, and `post_peak` as an operational price-route
hypothesis. The adapter verifies every day of that reference window and checks
that the configured peak is its first highest high. It does not identify all
completed cycles, infer a phase from calendar rollover, or establish that the
latest measured high is a final cycle top. Another justified reference window
and phase can be supplied without changing code.

Both the reference window and the interval from the previous peak through the
latest closed UTC day must be complete. Identity, checksum, duplicate/open days,
OHLC and volume are validated by the archive loader. The existing selector then
validates phase, strict new highs/lows, separate-candle ordering and shared
macroanchors. An active configuration with incomplete/corrupt history, an invalid
peak or missing configuration fields explicitly supplies unavailable context:
the route layer cannot silently reuse its shorter observed range.
Unreadable, missing or unknown configuration also suppresses macro readings;
only an explicitly valid draft/disabled configuration leaves the v4 routes active.

## Provenance and time

Reviews bind the exact configuration and normalized archive content with SHA-256,
and retain retrieval-page URLs/timestamps separately from local validation time.
`source.observed_at` in the adapter contract means local archive validation, with
`observation_kind=local_archive_validation`; it is **not a new API observation**.
Completeness through the latest closed UTC day is independently rechecked on
every collection. A new missing day suppresses the candidate until the separate
daily history workflow fills it. Between midnight and that workflow, unavailable
coverage can therefore be expected; no old green status is carried forward.

Draft reviews omit the full candle/evidence array. An active original context
retains the required OHLC candles, page provenance and configuration hashes in
its frozen evidence. Existing original snapshots are not rewritten. Original
anchor version IDs still change on strict new extrema/phase changes, rather than
on every collection or wording clarification.

Read-only review, with an explicit assessment time:

```sh
python -m scripts.cycle_context --as-of 2026-10-24T22:01:55.667737+00:00
```

Using the checked-in archive at that historical assessment time, the proposed
reference is 69,145.5 USDT on the 2021-11-10 UTC day; the highest later daily high
is 126,173.6 on 2025-10-06; the lowest subsequent daily low is 57,770 on 2026-07-01.
These are Bitget BTCUSDT USDT-FUTURES observations from this source, not a lifetime
spot ATH or proof of a confirmed cycle bottom. At later assessment times the
archive must include the additional closed days or the review is unavailable.

## Checkpoint and next step

The original NAS snapshot ending 2026-10-24T22:01:55.667737+00:00 confirms complete
`cycle_history_reference` metadata: 2,122 days through 2026-10-23, no missing days,
archive SHA-256 `42733ee6f74db2fb58ee53ed957ff89cce4989af73dda664d27feccb3305cf45`.
This proves incorporation of #63 source metadata, not operation of this adapter.
The adapter is merged in PR #65 (46dd127), and handover PR #64 is merged
(7cd2b1a). Post-merge Pages publication and a new automatic NAS review still
require separate verification. The latest checked NAS snapshot predates #65. Next: inspect an original
automatic draft review, review the proposed reference/phase, then activate in a
separate configuration change if appropriate. Browser visual QA remains open.
