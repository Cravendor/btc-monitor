# CVD volume mismatch investigation — 25 October 2026

## Observed result

The original NAS upload at 08:02 UTC rejected spot and USDT-futures recovery for
04:00–08:00 UTC with candle_volume_mismatch. That summary did not publish the
numerical discrepancies. Earlier successful windows are present in actual
snapshots; this was not evidence that all CVD had failed for days.

A new direct public-API retrieval of this SAME interval, paginated through the
terminal empty page, produced the following exact Decimal comparisons:

| Market | Trades | Pages including empty | BTC volume, both sources | USDT volume, both sources | Buy minus sell, BTC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Spot | 12,270 | 14 | 179.786083 | 14508401.55937062 | -4.374325 |
| USDT-futures | 47,160 | 49 | 1832.2347 | 147751103.71966 | -223.2247 |

The public-history evidence was independently replayed by cvd_coverage against
an isolated EMPTY test journal. Its missing-journal counts consequently describe
the research fixture, not the user's NAS. Neither raw research trades nor that
fixture is published. There was no write/access to the live NAS journal.

Separately, actual NAS commit 57d7173 contains the original 08:32 UTC snapshot
(data/2026/10/25/20261025T083216553390Z-local-1.json). BOTH markets passed v1
coverage verification for the SAME 04:00–08:00 UTC interval with the same counts
and deltas. The existing next-half-hour recovery therefore succeeded without
loosening the validator or installing the accompanying proposed code.

## What is established, and what is not

Exact matching is achievable. This investigation found NO basis for an arbitrary
percentage tolerance or treating quote mismatches as normal rounding. Previous
NAS-backed examples also matched exactly. Bitget's public futures history API
provides paginated trades within 90 days, with up to 1,000 entries per page;
that does not mean one response contains the full history.

A transient difference in delivered history/candle evidence near a 4H boundary
is consistent with these observations. Cache timing, provider finalization and
specific original missing trades cannot be distinguished from the original short
log. The private candidate reports contain original totals; the accompanying
change exports only safe aggregate diagnostics, including prior mismatches for
the same interval, automatically on the next ordinary NAS upload. Do NOT call
provider cache lag a proven root cause before reading those original numbers.

Historical OPEN gap markers can overlap many future intervals. The unchanged
49/84 counters are not 49/84 newly observed disconnects in every window and do
not invalidate a separately verified historical interval. The UI now makes this
explicit. Provider-reported side remains separate from independently verified
aggressor-side or market-wide CVD.

## Change and acceptance

Retain exact BTC AND quote equality. On mismatch, re-request the same candle
using endTime=end+1, then select it by its original open timestamp; never use a
neighboring/current candle. The documented endpoint can return an additional
candle when endTime exceeds a boundary, so timestamp selection is mandatory.
Preserve original and refreshed candle rows locally. Unexplained differences,
wrong intervals, exhausted budgets and journal conflicts continue to fail closed.
Publish numerical discrepancies as unverified diagnostics, not as a valid delta.

Fixtures test stale-then-correct candle responses, persistent tiny quote mismatch,
read-only source replay and public-safe diagnostics. This proves those code paths,
not that the new retry has already resolved a real live cache incident.

Primary references checked 25 October 2026:
- https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market
  (public history pagination, base/quote candle fields, endTime boundary behavior)
- https://www.bitget.com/docs/catalog/market/market-data
  (public market-data scope; do not silently apply V3 semantics to V2)
