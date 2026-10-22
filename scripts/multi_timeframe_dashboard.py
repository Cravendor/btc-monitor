"""Static read-only multi-timeframe BTC signal table from latest.json."""
import html
import json
from pathlib import Path

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"slightly_bearish": "Licht bearish", "bearish": "Bearish",
          "slightly_bullish": "Licht bullish", "bullish": "Bullish",
          "neutral": "Neutraal", "strongly_bullish": "Sterk bullish",
          "strongly_bearish": "Sterk bearish"}


def render(feed):
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
        rows.append("<tr><th>" + html.escape(tf.upper()) + "</th><td>" +
                    html.escape(grade) + "</td><td>" + html.escape(confidence) +
                    "</td><td>" + html.escape(str(observed)) + "</td></tr>")
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTC Multi-timeframe Signals</title>
<style>body{font:16px system-ui;background:#101827;color:#eef3ff;
max-width:960px;margin:2rem auto;padding:1rem}
section{background:#1c2940;padding:1.4rem;border-radius:16px;overflow:auto}
table{width:100%;border-collapse:collapse}th,td{padding:.8rem;
text-align:left;border-bottom:1px solid #44536d}p{color:#bac8da}</style>
<h1>BTC — Multi-timeframe marktrichting</h1>\n<p><a href="btc-signal-history.html" style="color:#93c5fd">Bekijk historische signaaltijdlijn →</a></p>
<section><table><thead><tr><th>Timeframe</th><th>Signaal</th>
<th>Betrouwbaarheid</th><th>Afgesloten candle (UTC)</th></tr></thead>
<tbody>""" + "".join(rows) + """</tbody></table></section>
<p>Alle scores zijn voorlopig, uitsluitend op prijsstructuur gebaseerd.
Volume is context, geen richtingsbevestiging. Ontbrekende candles, CVD of
timeframes worden niet ingevuld. Geen handelsadvies.</p></html>"""


def build(feed_path, output):
    try:
        feed = json.loads(Path(feed_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        feed = {}
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(feed), encoding="utf-8")


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2])
