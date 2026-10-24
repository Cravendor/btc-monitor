"""Static read-only multi-timeframe BTC signal table from latest.json."""
import html
import json
from pathlib import Path
from scripts.history_coverage import coverage_html

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"slightly_bearish": "Licht bearish", "bearish": "Bearish",
          "slightly_bullish": "Licht bullish", "bullish": "Bullish",
          "neutral": "Neutraal", "strongly_bullish": "Sterk bullish",
          "strongly_bearish": "Sterk bearish"}


EVIDENCE = {"aligned": "Trend en momentum eens", "conflicting": "Trend en momentum tegengesteld",
            "partial_direction": "Slechts één richtinggevend", "no_direction": "Geen duidelijke richting"}


def render(feed, health=None):
    health = health if isinstance(health, dict) else {}
    health_banner = ('<section><h2>Datakwaliteit — 24 uur</h2>' +
                     coverage_html(health.get("coverage_24h")) +
                     '<p>Watchdog laatst gecontroleerd: ' +
                     html.escape(str(health.get("checked_at") or "ONTBREEKT")) + '</p></section>')

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
text-align:left;border-bottom:1px solid #44536d}p{color:#bac8da;overflow-wrap:anywhere}
*{box-sizing:border-box}h1{font-size:clamp(1.5rem,5vw,2rem)}
section{max-width:100%;overscroll-behavior-x:contain}
@media(max-width:600px){body{margin:0 auto;padding:.8rem}section{padding:.6rem}
th,td{min-width:8rem;padding:.65rem}th:first-child{min-width:4rem;position:sticky;left:0;background:#1c2940}}</style>
<nav><a href="index.html" style="color:#93c5fd">← Overzicht en scenario’s</a> · <a href="btc-dashboard.html" style="color:#93c5fd">Dashboard</a></nav><h1>BTC — Multi-timeframe marktrichting</h1>\n<p><a href="btc-signal-history.html" style="color:#93c5fd">Bekijk historische signaaltijdlijn →</a></p>
""" + health_banner + """<p>Veeg de tabel horizontaal voor alle kolommen.</p><section tabindex="0" role="region" aria-label="Timeframes, horizontaal schuifbaar"><table><thead><tr><th>Timeframe</th><th>Signaal</th>
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

