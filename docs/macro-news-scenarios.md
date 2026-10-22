# Macro, News & Scenario Intelligence — implementation specification

Status: proposed design, not active data collection or validated signals. Budget: EUR 0.

## Data integrity
- Economic events: event_id, country, category, scheduled_at_utc, actual_release_at_utc, actual, consensus, previous, revision, unit, source_url, retrieved_at_utc, status.
- Event sources: Fed/FOMC, BLS, BEA, Census, Treasury, FRED, ECB and other official calendars. Consensus requires a verifiable separate source; never invent it.
- News: published_at_utc, discovered_at_utc, source_url, original vs commentary, event category, claimed causal mechanism, supporting/conflicting market observations.
- Preserve release-time vintages and revisions. No hindsight data leakage into historical backtests.
- No paid feeds. Unavailable or delayed information must be explicit.

## Technical levels
- Use completed OHLC candles, consistent venue, symbol, quote unit and UTC times.
- Provide linear Fibonacci and log Fibonacci retracements as separate methodologies. For positive endpoints low L and high H and retracement fraction r, linear descending level = H-r*(H-L); log descending level = exp(log(H)-r*(log(H)-log(L))).
- Record anchor times/prices, direction, timeframe, method, ratio, candle closure and invalidation. Do not select anchors retrospectively to improve apparent accuracy.
- Elliott Wave is a subjective, versioned candidate count, with alternate counts and clear invalidation, never a confirmed fact or standalone signal.
- Confluence: support/resistance, swing structure, volume, EMAs and Fib levels; account for correlated inputs.

## Scenario contract
- scenario_id, version, created_at_utc, timeframe, hypothesis (macro_bottom, complacency_distribution, range), prior assumptions, evidence_for, evidence_against, prerequisites, trigger levels, invalidation levels, event risks, status, confidence/coverage, and source references.
- Separate directional forecasts from structural/cycle confirmations; assign explicit outcome tests and horizons.
- Keep macro-cycle and trading-timeframe signals distinct.
- No price target without computed, auditable anchor data.
- No precise probabilities unless historically calibrated on out-of-sample data.

## Learning loop
- Freeze the full original feature set and model version at issue time.
- Evaluate at predeclared 4h/24h/7d/30d horizons using appropriate same-market observations; missing observations remain unevaluated.
- Measure false positives, missed events, calibration, returns, regime stability, and class imbalance, not just accuracy.
- Use chronological walk-forward tests and embargo for overlapping outcomes. Avoid hindsight wave-counting and event revisions.
- Challenger models run in shadow mode; no unattended production changes. Require reproducible improvement, sufficient sample and approval.

## Implementation sequence
1. Read-only event and news schema + provenance validation.
2. Event calendar ingestion and economic surprise logic.
3. Price level engine with linear/log Fib and swing anchors.
4. Candidate Elliott Wave annotations with alternate counts.
5. Scenario generation and confirmation/invalidation state machine.
6. Historical outcomes and challenger validation.
7. GitHub Pages display and existing monitor integration.

All modules must tolerate absent sources and maintain historical logging. Never equate an official event calendar with guaranteed real-time news delivery.
