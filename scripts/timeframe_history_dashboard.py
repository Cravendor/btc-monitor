"""Read-only BTC signal history HTML with explicit missing-data states."""
import html
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"bearish": "Bearish", "slightly_bearish": "Licht bearish",
          "neutral": "Neutraal", "slightly_bullish": "Licht bullish",
          "bullish": "Bullish"}



def summarize(records, hours):
    """Summarize observed snapshots only; no inference for missing intervals."""
    valid = []
    for entry in records:
        try:
            stamp = datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is not None:
                valid.append((stamp.astimezone(timezone.utc), entry))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    if not valid:
        return None
    end = max(t for t, _ in valid)
    start = end - timedelta(hours=hours)
    # Require coverage across the requested window, not just two nearby snapshots.
    window = sorted(((t, r) for t, r in valid if start <= t <= end), key=lambda x: x[0])
    if len(window) < 2 or window[0][0] > start + timedelta(hours=min(hours / 4, 4)):
        return None
    output = {}
    for tf in TIMEFRAMES:
        observed = []
        for _, row in window:
            signal = (row.get("signals") or {}).get(tf) or {}
            grade = signal.get("grade") if signal.get("status") == "ok" else None
            if grade in LABELS:
                observed.append(grade)
        changes = sum(a != b for a, b in zip(observed, observed[1:]))
        output[tf] = {"observations": len(observed), "changes": changes,
                      "bullish": sum(g in ("bullish", "slightly_bullish") for g in observed),
                      "bearish": sum(g in ("bearish", "slightly_bearish") for g in observed),
                      "neutral": observed.count("neutral")}
    return output


def summary_html(records):
    sections = []
    for label, hours in (("24 uur", 24), ("7 dagen", 168), ("30 dagen", 720)):
        stats = summarize(records, hours)
        if stats is None:
            sections.append("<h2>" + label + "</h2><p>ONTBREEKT — onvoldoende historische dekking.</p>")
            continue
        rows = []
        for tf, item in stats.items():
            rows.append("<tr><th>" + tf.upper() + "</th><td>" + str(item["observations"]) +
                        "</td><td>" + str(item["bullish"]) + "</td><td>" +
                        str(item["neutral"]) + "</td><td>" + str(item["bearish"]) +
                        "</td><td>" + str(item["changes"]) + "</td></tr>")
        sections.append("<h2>" + label + "</h2><p>Aantallen snapshots, geen tijdgewogen percentages.</p>" +
                        "<main><table><tr><th>TF</th><th>Metingen</th><th>Bull</th><th>Neutraal</th><th>Bear</th><th>Wissels</th></tr>" +
                        "".join(rows) + "</table></main>")
    return "".join(sections)


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
""" + summary_html(records) + """<main><table><thead><tr><th>Meting (UTC)</th>""" + head + "</tr></thead><tbody>" + body + "</tbody></table></main></html>"


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
