# BTC Market Bias history (free, opt-in)

This feature does not change the existing Bitget collector or any ChatGPT automation.

## Archive format
Each report must be a verified JSON object with `schema_version: 1`, `monitor` one of `daily`, `4h-warning`, `market-risk`, an ISO8601 timezone-aware `reported_at`, a `sources` list of HTTPS URLs, and a `bias` object with three horizons: `4h_1d`, `7d`, `30d_macro`. Each horizon has `score` (-2 through +2, or null), `reason`, and `status: "ONVOLDOENDE DATA"` if score is null. Scores are interpretations from the originating report, **not automatically calculated from Bitget metrics**. Never backfill guessed historical opinions.

Example (illustrative only; DO NOT archive as real evidence):
```json
{
  "schema_version": 1,
  "monitor": "daily",
  "reported_at": "2026-10-21T17:00:00+02:00",
  "sources": ["https://github.com/Cravendor/btc-monitor"],
  "bias": {
    "4h_1d": {"score": 1, "reason": "Illustrative example only"},
    "7d": {"score": 0, "reason": "Illustrative example only"},
    "30d_macro": {"score": null, "status": "ONVOLDOENDE DATA", "reason": "Illustrative example only"}
  }
}
```

## Activation
After merging, go to **Actions → Archive BTC bias report → Run workflow** and paste an actual validated report JSON. The workflow checks its schema and writes to `reports/YYYY/MM/DD/monitor-HHMMSS.json` plus `reports/index.json`. No paid APIs or hosting. The Pages dashboard at `/bias.html` reads the index. Before the first archived report it shows zero reports.

**Important:** ChatGPT scheduled tasks are NOT automatically linked to this GitHub Actions workflow. Automatic archiving requires a separately authenticated and tested bridge; do not claim that reports are being archived until such a bridge exists. The archive action must be triggered with real data; it must not synthesize a rating from the market feed. The GitHub Actions input and archive are public, so never include private data or secrets.

## Validation and reliability
Scores: -2 strong bearish, -1 weak bearish, 0 neutral, +1 weak bullish, +2 strong bullish; null means insufficient data, not neutral. A report is never overwritten. The index is rebuilt from archived reports; report dates are UTC-based. In the initial dashboard, 24h/7d/30d filters show individual observations, not aggregate consensus or prediction accuracy. No reports = no history.

## Cost
Public repository, standard GitHub-hosted runner, Pages. Budget €0. No paid service is activated.
