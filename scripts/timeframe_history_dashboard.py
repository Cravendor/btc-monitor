"""Read-only BTC signal history HTML with explicit missing-data states."""
import html
import json
from pathlib import Path

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"bearish": "Bearish", "slightly_bearish": "Licht bearish",
          "neutral": "Neutraal", "slightly_bullish": "Licht bullish",
          "bullish": "Bullish"}


def render(records):
    rows = []
    for item in sorted(records, key=lambda r: r.get("updated_at", ""), reverse=True)[:100]:
        when = html.escape(str(item.get("updated_at", "ONTBREEKT")))
        cells = []
        for tf in TIMEFRAMES:
            signal = (item.get("signals") or {}).get(tf) or {}
            grade = signal.get("grade") if signal.get("status") == "ok" else None
            label = LABELS.get(grade, "ONTBREEKT")
            css = "bull" if grade in ("bullish", "slightly_bullish") else "bear" if grade in ("bearish", "slightly_bearish") else "neutral"
            cells.append('<td class="' + css + '">' + html.escape(label) + '</td>')
        rows.append("<tr><th>" + when + "</th>" + "".join(cells) + "</tr>")
    head = "".join("<th>" + tf.upper() + "</th>" for tf in TIMEFRAMES)
    body = "".join(rows) if rows else '<tr><td colspan="8">Nog geen geldige historische metingen.</td></tr>'
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTC historische signaaltijdlijn</title>
<style>body{font:15px system-ui;background:#101827;color:#eef3ff;max-width:1200px;margin:2rem auto;padding:1rem}
main{overflow-x:auto;background:#1c2940;padding:1rem;border-radius:16px}
table{border-collapse:collapse;width:100%;white-space:nowrap}
td,th{padding:.65rem;text-align:left;border-bottom:1px solid #44536d}
.bull{color:#86efac}.bear{color:#fca5a5}.neutral{color:#cbd5e1}
p{color:#bac8da}</style><h1>BTC — Historische signaaltijdlijn</h1>
<p>Laatste 100 opgeslagen snapshots, nieuwste bovenaan. Alle signalen zijn voorlopig;
dit is geen backtest. Tijdstempels zijn UTC. Ontbrekende gegevens blijven ONTBREEKT.</p>
<main><table><thead><tr><th>Meting (UTC)</th>""" + head + "</tr></thead><tbody>" + body + "</tbody></table></main></html>"


def build(source, output):
    records = []
    path = Path(source)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
                if isinstance(entry, dict) and isinstance(entry.get("signals"), dict):
                    records.append(entry)
            except ValueError:
                continue
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(records), encoding="utf-8")


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2])
