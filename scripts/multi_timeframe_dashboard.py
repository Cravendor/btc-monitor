"""Static read-only multi-timeframe BTC signal table from latest.json."""
import html
import json
from pathlib import Path

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"slightly_bearish": "Licht bearish", "bearish": "Bearish",
          "slightly_bullish": "Licht bullish", "bullish": "Bullish",
          "neutral": "Neutraal", "strongly_bullish": "Sterk bullish",
          "strongly_bearish": "Sterk bearish"}


EVIDENCE = {"aligned": "Trend en momentum eens", "conflicting": "Trend en momentum tegengesteld",
            "partial_direction": "Slechts één richtinggevend", "no_direction": "Geen duidelijke richting"}


def render(feed, health=None):
    health = health if isinstance(health, dict) else {}
    coverage = health.get("coverage_24h")
    coverage_text = "ONTBREEKT"
    if isinstance(coverage, dict):
        observed = coverage.get("observed_snapshots")
        expected = coverage.get("expected_snapshots")
        if type(observed) is int and type(expected) is int and 0 <= observed and expected > 0:
            coverage_text = f"{observed}/{expected} ({100 * observed / expected:.1f}%)"
    health_banner = ('<section><h2>Datakwaliteit</h2><p>24-uursdekking: ' +
                     html.escape(coverage_text) +
                     ' opgeslagen snapshots. Deze historische dekking is geen signaalzekerheid.</p>' +
                     '<p>Watchdog laatst gecontroleerd: ' +
                     html.escape(str(health.get("checked_at") or "ONTBREEKT")) +
                     ' UTC/offset</p></section>')

    measurement = (feed.get("measurements") or [{}])[0]
    metrics = measurement.get("metrics") or {}
    multi = (metrics.get("multi_timeframe") or {}).get("data") or {}
    rows = []
    for tf in TIMEFRAMES:
        item = multi.get(tf) or {}
        signal = item.get("signal") or {}
        valid = item.get("status") == "ok" and signal.get("status") == "provisional"
        grade = LABELS.get(signal.get("grade"), "ONTBREEKT") if valid else "ONTBREEKT"
        confidence = "Laag (prijs-only)" if valid else "Geen"
        observed = signal.get("observed_at") if valid else "—"
        evidence = EVIDENCE.get((signal.get("evidence") or {}).get("state"), "ONTBREEKT") if valid else "ONTBREEKT"
        freshness = ('<span class="candle-freshness" data-closed="' +
                     html.escape(str(observed), quote=True) + '" data-period-min="' +
                     str({"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240,
                          "1d": 1440, "1w": 10080}[tf]) +
                     '">CONTROLEREN</span>') if valid else "GEEN CANDLE"
        rows.append("<tr><th>" + html.escape(tf.upper()) + "</th><td>" +
                    html.escape(grade) + "</td><td>" + html.escape(evidence) + "</td><td>" + html.escape(confidence) +
                    "</td><td>" + html.escape(str(observed)) + "</td><td>" + freshness + "</td></tr>")
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTC Multi-timeframe Signals</title>
<style>body{font:16px system-ui;background:#101827;color:#eef3ff;
max-width:960px;margin:2rem auto;padding:1rem}
section{background:#1c2940;padding:1.4rem;border-radius:16px;overflow:auto}
table{width:100%;border-collapse:collapse}th,td{padding:.8rem;
text-align:left;border-bottom:1px solid #44536d}p{color:#bac8da}</style>
<h1>BTC — Multi-timeframe marktrichting</h1>\n<p><a href="btc-signal-history.html" style="color:#93c5fd">Bekijk historische signaaltijdlijn →</a></p>
""" + health_banner + """<section><table><thead><tr><th>Timeframe</th><th>Signaal</th>
<th>Onderbouwing</th><th>Betrouwbaarheid</th><th>Afgesloten candle (UTC)</th><th>Candle-actualiteit</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table></section>
<p>Alle scores zijn voorlopig en gebaseerd op prijs en volume. Een neutrale score kan ook tegenstrijdig bewijs betekenen.
Volume is context, geen richtingsbevestiging. Ontbrekende candles, CVD of
timeframes worden niet ingevuld. Geen handelsadvies.</p>
<p>Actualiteit wordt in de browser berekend. Een afgesloten candle is verouderd
wanneer deze ouder is dan twee volledige timeframe-perioden plus vijf minuten.
Dit is geen validatie van orderflow of modelbetrouwbaarheid.</p>
<script>
(function () {
  function refresh() {
    document.querySelectorAll(".candle-freshness").forEach(function (el) {
      var timestamp = Date.parse(el.dataset.closed);
      var period = Number(el.dataset.periodMin);
      var age = (Date.now() - timestamp) / 60000;
      el.textContent = !Number.isFinite(timestamp) || !Number.isFinite(period) ||
        period <= 0 || age < -5 ? "ONGELDIGE TIJD" :
        age > 2 * period + 5 ? "VEROUDERD" : "ACTUEEL";
    });
  }
  refresh();
  setInterval(refresh, 60000);
})();
</script></html>"""


def build(feed_path, output, health_path=None):
    try:
        feed = json.loads(Path(feed_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        feed = {}
    try:
        health = json.loads(Path(health_path).read_text(encoding='utf-8')) if health_path else None
    except (OSError, ValueError):
        health = None
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(feed, health), encoding="utf-8")


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
