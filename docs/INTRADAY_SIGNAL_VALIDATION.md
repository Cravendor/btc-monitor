# Intraday signal retrospective validation

Market: Bitget BTCUSDT USDT-FUTURES; as of 2026-10-29T04:44:40.223237+00:00; common closed coverage through 2026-10-27T16:00:00+00:00. The 4H and 1H archives are partial after this boundary. Sources are current archives that may include later provider revisions: this is not point-in-time proof. No historical CVD or other exchanges are used.

24 closed native candles per signal; outcomes at 24 hours and seven days. Chronological non-overlapping observations, exclude outcomes crossing the 2026 split. 2026 has already been examined in previous exploration, so it is not an independent holdout. Same-close reference is not an executable trading price. No fees, tuning, probabilities or trading claims.

## 1H

Native archive SHA256 `79e771c7109a9265b6c9394ce150bb70eec76cddd56f62cfa6ce24b94df07777`; 11608 candles; archive status partial; closed through 2026-10-27T16:00:00+00:00.

### 24 hours

| Period | Signal | Count | Positive | Negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| 2025 | bearish | 1 | 0 | 1 | -1.7499 |
| 2025 | bullish | 1 | 1 | 0 | 1.9145 |
| 2025 | neutral | 138 | 68 | 70 | -0.0271 |
| 2025 | slightly_bearish | 23 | 11 | 12 | -0.3759 |
| 2025 | slightly_bullish | 20 | 10 | 10 | -0.1598 |
| 2026 | bearish | 4 | 1 | 3 | -1.1765 |
| 2026 | bullish | 4 | 1 | 3 | -0.2301 |
| 2026 | neutral | 219 | 104 | 115 | -0.1516 |
| 2026 | slightly_bearish | 34 | 21 | 13 | 1.0659 |
| 2026 | slightly_bullish | 38 | 18 | 20 | 0.0463 |

Baseline over all sampled signals:
- 2025: 183 observations, 90 positive, mean -0.0842%.
- 2026: 299 observations, 145 positive, mean -0.0028%.

### 168 hours

| Period | Signal | Count | Positive | Negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| 2025 | neutral | 18 | 11 | 7 | -0.1212 |
| 2025 | slightly_bearish | 4 | 2 | 2 | -0.9546 |
| 2025 | slightly_bullish | 4 | 0 | 4 | -2.1566 |
| 2026 | bearish | 1 | 0 | 1 | -4.1100 |
| 2026 | neutral | 32 | 15 | 17 | -0.0598 |
| 2026 | slightly_bearish | 6 | 3 | 3 | -1.1399 |
| 2026 | slightly_bullish | 3 | 2 | 1 | 5.4489 |

Baseline over all sampled signals:
- 2025: 26 observations, 13 positive, mean -0.5625%.
- 2026: 42 observations, 20 positive, mean 0.0830%.

## 4H

Native archive SHA256 `466e81118afcb4005f56d14ae5ae8fdd4f91a8eaa00ae7749ac4f23303ccbad1`; 2902 candles; archive status partial; closed through 2026-10-27T16:00:00+00:00.

### 24 hours

| Period | Signal | Count | Positive | Negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| 2025 | bearish | 6 | 3 | 3 | 0.8639 |
| 2025 | bullish | 5 | 3 | 2 | 0.6099 |
| 2025 | neutral | 79 | 38 | 41 | -0.0444 |
| 2025 | slightly_bearish | 46 | 24 | 22 | -0.4062 |
| 2025 | slightly_bullish | 44 | 20 | 24 | -0.0831 |
| 2026 | bearish | 12 | 6 | 6 | 1.4430 |
| 2026 | bullish | 11 | 5 | 6 | 0.7085 |
| 2026 | neutral | 135 | 70 | 65 | -0.0082 |
| 2026 | slightly_bearish | 71 | 32 | 39 | -0.2166 |
| 2026 | slightly_bullish | 70 | 32 | 38 | -0.1352 |

Baseline over all sampled signals:
- 2025: 180 observations, 88 positive, mean -0.0979%.
- 2026: 299 observations, 145 positive, mean -0.0028%.

### 168 hours

| Period | Signal | Count | Positive | Negative | Mean return % |
| --- | --- | ---: | ---: | ---: | ---: |
| 2025 | bearish | 2 | 1 | 1 | -1.3216 |
| 2025 | neutral | 9 | 4 | 5 | 1.5574 |
| 2025 | slightly_bearish | 8 | 4 | 4 | -0.4551 |
| 2025 | slightly_bullish | 6 | 1 | 5 | -4.2203 |
| 2026 | bearish | 3 | 0 | 3 | -6.5554 |
| 2026 | bullish | 2 | 2 | 0 | 10.4247 |
| 2026 | neutral | 15 | 9 | 6 | 0.9970 |
| 2026 | slightly_bearish | 12 | 7 | 5 | 0.6933 |
| 2026 | slightly_bullish | 10 | 2 | 8 | -2.0973 |

Baseline over all sampled signals:
- 2025: 25 observations, 10 positive, mean -0.7036%.
- 2026: 42 observations, 20 positive, mean 0.0830%.

The selection starts at the earliest usable sample; other sampling phases can produce different results. Samples retain dependence and small groups, especially strong grades, do not support confident ranking. Never interpret matching rows or this report as calibrated probabilities. Further work: phase sensitivity, uncertainty, source revision provenance and a truly untouched forward interval.
