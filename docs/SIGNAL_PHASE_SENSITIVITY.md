# Sensitivity to sampling phase

2026 native Bitget BTCUSDT USDT-FUTURES price/volume data through 2026-10-27T16:00:00+00:00; archive hashes: 1H `79e771c7109a9265b6c9394ce150bb70eec76cddd56f62cfa6ce24b94df07777`; 4H `466e81118afcb4005f56d14ae5ae8fdd4f91a8eaa00ae7749ac4f23303ccbad1`. Generated at 2026-10-29T04:48:38.200260+00:00. These are current archival values, potentially later revised; CVD and other exchanges are absent.

Within each phase, sample non-overlapping windows after a 24-candle signal. Compare every hourly or four-hourly phase for 24h and 7d horizons. A rate is suppressed when a phase has fewer than 10 observations. The phases overlap each other and cannot be counted as independent trials. The 2026 data have been explored previously.

| Timeframe | Horizon | Grade | Phases with >=10 | Positive-rate range across phases | Sample range across phases |
| --- | ---: | --- | ---: | --- | --- |
| 1h | 24h | bearish | 5/24 | 40.0%–55.6% | 2–20 |
| 1h | 24h | bullish | 3/24 | 43.8%–56.2% | 1–16 |
| 1h | 24h | neutral | 24/24 | 47.5%–56.2% | 145–229 |
| 1h | 24h | slightly_bearish | 24/24 | 34.8%–61.8% | 26–63 |
| 1h | 24h | slightly_bullish | 24/24 | 34.9%–62.5% | 31–74 |
| 1h | 168h | bearish | 0/168 | insufficient | 1–7 |
| 1h | 168h | bullish | 0/168 | insufficient | 1–6 |
| 1h | 168h | neutral | 168/168 | 23.5%–60.9% | 12–42 |
| 1h | 168h | slightly_bearish | 30/168 | 18.2%–63.6% | 1–15 |
| 1h | 168h | slightly_bullish | 28/168 | 20.0%–72.7% | 1–20 |
| 4h | 24h | bearish | 5/6 | 50.0%–57.9% | 7–38 |
| 4h | 24h | bullish | 5/6 | 38.5%–69.2% | 9–36 |
| 4h | 24h | neutral | 6/6 | 44.9%–55.1% | 127–139 |
| 4h | 24h | slightly_bearish | 6/6 | 45.1%–56.1% | 44–82 |
| 4h | 24h | slightly_bullish | 6/6 | 38.5%–54.8% | 43–78 |
| 4h | 168h | bearish | 0/42 | insufficient | 1–9 |
| 4h | 168h | bullish | 0/42 | insufficient | 1–9 |
| 4h | 168h | neutral | 42/42 | 20.0%–66.7% | 10–31 |
| 4h | 168h | slightly_bearish | 20/42 | 27.3%–70.0% | 3–17 |
| 4h | 168h | slightly_bullish | 20/42 | 20.0%–70.0% | 3–18 |

Ranges describe selected phases, not a probability interval or independent replications. Low counts, multiple comparisons and dependent market observations make phase extremes unstable. The program can provide Wilson 95% intervals for each phase with at least 10 observations; these are only iid-binomial approximations and are not valid guarantees under serial dependence. No thresholds or trading settings were tuned or activated. For a robust assessment use phase stability with block-based uncertainty and a genuinely untouched forward period.
