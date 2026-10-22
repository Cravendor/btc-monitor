"""Static read-only BTC 4H historical trend report."""
import html
import json
from pathlib import Path
from scripts.context_trends import trend_windows

WINDOWS = (("24h", "24 uur"), ("7d", "7 dagen"), ("30d", "30 dagen"))


def render(records, as_of):
    data = trend_windows(records, as_of)
    grade = data.get("current_grade") or "ONTBREEKT"
    rows = []
    for key, label in WINDOWS:
        item = data.get("windows", {}).get(key, {})
        if item.get("status") == "compared":
            change = item["grade_step_change"]
            trend = ("Bullisher" if change > 0 else "Bearisher" if change < 0
                     else "Ongewijzigd")
            value = f"{trend} ({change:+d})"
        else:
            value = "ONTBREEKT"
        rows.append("<tr><td>" + html.escape(label) + "</td><td>" +
                    html.escape(value) + "</td></tr>")
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTC 4H Historical Trends</title>
<style>body{font:16px system-ui;background:#101827;color:#eef3ff;max-width:850px;
margin:2rem auto;padding:1rem}section{background:#1c2940;padding:1.4rem;
border-radius:16px}td,th{padding:.9rem;text-align:left;border-bottom:1px solid #44536d}
table{width:100%;border-collapse:collapse}p{color:#bac8da}</style>
<h1>BTC 4H — Historische marktrichting</h1>
<section><p>Voorlopige prijsstructuur · lage betrouwbaarheid</p><h2>""" + html.escape(grade) + """</h2>
<table><thead><tr><th>Periode</th><th>Verandering</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></section>
<p>Ontbrekende metingen worden niet geïnterpoleerd. CVD en hypothesen A/B zijn niet bevestigd.</p>
</html>"""


def build(archive, output, as_of):
    source = Path(archive)
    records = ([json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()
                if line.strip()] if source.exists() else [])
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(records, as_of), encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("archive")
    p.add_argument("output")
    p.add_argument("--as-of", required=True)
    args = p.parse_args()
    build(args.archive, args.output, args.as_of)
