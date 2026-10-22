"""Produce a static, read-only HTML signal performance report from a frozen dataset.

No live trading, no invented measurements. Unavailable outcomes remain missing.
"""
import html
import json
from collections import defaultdict
from pathlib import Path


GRADES = ("strongly_bearish", "bearish", "slightly_bearish", "neutral",
          "slightly_bullish", "bullish", "strongly_bullish")


def summarize(rows):
    groups = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0,
                                  "flat": 0, "unavailable": 0})
    for row in rows:
        key = (str(row["timeframe"]), str(row["grade"]))
        if key[1] not in GRADES:
            raise ValueError("unknown seven-level grade")
        outcome = row.get("outcome") or {}
        status = outcome.get("status")
        verdict = outcome.get("verdict")
        bucket = ("unavailable" if status != "evaluated" else
                  verdict if verdict in ("correct", "incorrect", "flat") else "unavailable")
        groups[key]["total"] += 1
        groups[key][bucket] += 1
    result = []
    for (timeframe, grade), counts in sorted(groups.items()):
        directional = counts["correct"] + counts["incorrect"]
        result.append({"timeframe": timeframe, "grade": grade, **counts,
                       "hit_rate": round(100 * counts["correct"] / directional, 2)
                       if directional else None})
    return result


def render_html(rows):
    summary = summarize(rows)
    body = []
    for item in summary:
        rate = "ONTBREEKT" if item["hit_rate"] is None else f'{item["hit_rate"]:.2f}%'
        cells = [item["timeframe"], item["grade"], item["total"],
                 item["correct"], item["incorrect"], item["flat"],
                 item["unavailable"], rate]
        body.append("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in cells) + "</tr>")
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<title>BTC Signal Performance (historisch)</title>
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem;background:#101827;color:#e9eef8}
table{width:100%;border-collapse:collapse}th,td{padding:.7rem;border-bottom:1px solid #40506a;text-align:left}
th{color:#a8c9ff}p{color:#b5c2d7}table{overflow-x:auto;display:block}</style>
<h1>BTC Signal Performance</h1>
<p>Alleen opgeslagen signalen. Geen live koersdata. Ontbrekende uitkomsten tellen niet als neutraal.</p>
<table><thead><tr><th>Timeframe</th><th>Signaal</th><th>Totaal</th>
<th>Correct</th><th>Incorrect</th><th>Flat</th><th>Ontbreekt</th><th>Hit rate</th>
</tr></thead><tbody>""" + "".join(body) + """</tbody></table>
<p>Hit rate is beschrijvend, geen bewijs van voorspellend vermogen.
Hypothese A/B is nog niet afzonderlijk gevalideerd.</p></html>"""


def build_report(dataset_path, output_path):
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expected JSON array of frozen history rows")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(data), encoding="utf-8")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("output")
    args = parser.parse_args()
    build_report(args.dataset, args.output)
