# One-off Bitget conflict-window recheck

The history workflow can re-request the exact BTCUSDT USDT-FUTURES native 4H
candle opening 27 October 2026 12:00 UTC and all four native hourly candles ending
at 16:00 UTC. At most two public Bitget requests are made per attempted run,
with the existing 15-second per-request timeout and no credentials. A fully
validated result ends further requests for this fixed window; incomplete or
unavailable results remain explicit and may be retried by the existing workflow.
No new schedule or NAS task is added.

The immutable content-addressed record retains exact returned OHLC/base/quote
strings, query URLs, observed times, the archived normalized values and archive
hashes. It compares 4H with the four hourly values using Decimal arithmetic,
and separately lists every change against cached normalized rows. Price and base
volume consistency is distinct from quote-volume diagnostics. Missing, malformed,
stale, duplicate or inconsistent responses and missing archives remain
`incomplete`, never a successful match. The probe does not alter archives, relax
source checks, substitute aggregated candles, infer why Bitget changed data, or
automatically activate any revision. SHA-256 provides integrity, not signature or
independent provider corroboration.

The existing workflow commits new source-window audits to main and uploads the
current record as a 30-day artifact even if later publication fails. A checked
result stops repeated requests, whether it finds agreement or conflict. Actual
failed-push recovery remains untested. If fresh prices and volume agree and differ
from cached values, the evidence supports a separate reviewed correction; the
correction and preservation of original versions are not part of this probe. If
the feeds still conflict, neither value is chosen. Actual public API results and
workflow acceptance must be observed after merge; mocked tests do not establish
the provider's current values.
