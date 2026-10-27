# 27 October 2026 — 4H / 1H source conflict

## Evidence and scope

The native Bitget BTCUSDT USDT-FUTURES 4H candle for 12:00–16:00 UTC was collected at 16:02:18.489 UTC on 27 October. The corresponding native 1H candles were collected at 16:02:18.812 UTC. Strict aggregation reports:

| Field | Native 4H | Four native 1H candles |
| --- | ---: | ---: |
| Close, USDT | 80459.3 | 80523.4 |
| Base volume, BTC | 6965.3543 | 7626.8427 |

Open, high and low agree. No synthetic replacement or relaxed tolerance is authorized by this finding.

The [automatic revision audit](../data/history/source-revision-audits/20261027T160219Z-5681b9ec34c2a72576030d5a17ea0265f1319fa6714ce45c433f66cb0cabbdf8.json) re-requested the latest two closed 4H and 1H candles at 16:02:20 UTC. It independently reproduced the cached 4H row and 14:00/15:00 UTC hourly rows in its bounded window. This is a second query to the same provider, not an independent market source. In particular the 15:00 hourly close 80523.4 and 4H close 80459.3 differ in the captured raw provider rows. The audit did not freshly re-request the 12:00 and 13:00 hourly rows, so it cannot independently revalidate all four contributing volumes. Its unchanged status means the selected individual cache rows match their re-query; it does NOT mean the timeframes reconcile or that the provider's final values are correct.

The [history workflow](https://github.com/Cravendor/btc-monitor/actions/runs/40536901001) reported this conflict and exited 1 after preserving the collector checkpoints and audit; its evidence artifact uploaded successfully. The source gate correctly blocks the affected 4H Elliott view. This event does not establish that the separate NAS trade collector stopped.

At the later 17:51 UTC offline build, the 16:00 hourly candle was missing relative to that build's cutoff. It was not missing relative to the 16:02 run's 16:00 cutoff. No current completeness claim is implied.

## Remaining decision

The provider's reason, whether this was a finalization delay, and which row is correct remain unknown. An attempted fresh public API retrieval from the present execution environment was unavailable. Wait for a successful fresh capture of the exact 12:00–16:00 4H and all four hourly candles, and replay original query windows if accessible. Preserve raw responses, query and observation times and prior archive hashes, then reconcile OHLC and BTC volume. A changed row requires a separate reviewed correction with original values retained; no automatic activation, NAS change or bypass of the source gate.

The existing history workflow is triggered by its existing schedule and eligible upstream workflow completions. Its next actual run and result must be observed, not assumed. Audit tail selection may no longer include this 12:00 candle on a later run; unchanged tails alone do not resolve this historical discrepancy.
