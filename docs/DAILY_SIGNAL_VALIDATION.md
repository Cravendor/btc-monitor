# Daily BTC signal retrospective validation

Scope: existing `multi_tf_evidence_v0.2` price/volume-only 1D signal on Bitget BTCUSDT USDT-FUTURES; no CVD, spot orderflow or other timeframes. This is a retrospective diagnostic on the current historical archive, not a point-in-time proof of what was known then, a trading simulation, calibration or a forecast. No thresholds were tuned.

Input SHA256: `4ca1a5e51cdd259221e7439fad8a1506d18e359468cd6464d86b8274e7086a01`; closed through 2026-10-28T00:00:00+00:00; generated as of 2026-10-29T04:40:14.896966+00:00.

Use 24 closed candles for each signal; compare the following one or seven complete daily closes. Consecutive evaluation intervals do not overlap. Outcomes spanning the 2026-01-01 UTC split are excluded; 2021–2025 is descriptive development history and 2026 is a chronological evaluation period, but it has already been inspected in an earlier exploratory probe and is not an independent untouched holdout. Same-close entry is a measurement convention, not an executable price. Current archive versions may reflect later exchange revisions. No trading costs, confidence intervals or probability claims.

## Horizon: 1 days

| Period | Signal | Count | Subsequent positive | Subsequent negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| development_2021_2025 | bearish | 178 | 102 | 76 | 0.2727 |
| development_2021_2025 | bullish | 144 | 81 | 63 | 0.4117 |
| development_2021_2025 | neutral | 509 | 246 | 263 | -0.0669 |
| development_2021_2025 | slightly_bearish | 441 | 233 | 208 | 0.1818 |
| development_2021_2025 | slightly_bullish | 530 | 243 | 287 | 0.0537 |
| holdout_2026 | bearish | 28 | 9 | 19 | -1.1714 |
| holdout_2026 | bullish | 25 | 10 | 15 | -0.0363 |
| holdout_2026 | neutral | 86 | 46 | 40 | 0.2229 |
| holdout_2026 | slightly_bearish | 79 | 41 | 38 | 0.1813 |
| holdout_2026 | slightly_bullish | 82 | 40 | 42 | -0.0058 |

Baseline across all sampled labels:
- development_2021_2025: 1802 observations, 905 positive, average 0.1012%.
- holdout_2026: 300 observations, 146 positive, average -0.0023%.

## Horizon: 7 days

| Period | Signal | Count | Subsequent positive | Subsequent negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| development_2021_2025 | bearish | 11 | 7 | 4 | 2.2948 |
| development_2021_2025 | bullish | 7 | 4 | 3 | 2.2703 |
| development_2021_2025 | neutral | 77 | 38 | 39 | 0.6136 |
| development_2021_2025 | slightly_bearish | 70 | 39 | 31 | 0.5716 |
| development_2021_2025 | slightly_bullish | 92 | 45 | 47 | 0.5428 |
| holdout_2026 | bearish | 4 | 0 | 4 | -3.5815 |
| holdout_2026 | bullish | 4 | 1 | 3 | 0.4862 |
| holdout_2026 | neutral | 16 | 9 | 7 | 0.6089 |
| holdout_2026 | slightly_bearish | 7 | 4 | 3 | -0.0564 |
| holdout_2026 | slightly_bullish | 11 | 6 | 5 | 0.5926 |

Baseline across all sampled labels:
- development_2021_2025: 257 observations, 133 positive, average 0.6939%.
- holdout_2026: 42 observations, 20 positive, average 0.0830%.

Results depend on start-date sampling and observed regime; small groups, residual dependence and revised data preclude confident ranking. In particular the seven-day 2026 strong-label samples contain only four observations each. Results do not validate other timeframes or derivative data. Do not activate new thresholds based on this report. Next compare competing candidates with a fixed development procedure and a genuinely untouched later out-of-sample period, uncertainty and regime-aware tests.
