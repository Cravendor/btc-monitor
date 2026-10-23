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



SCORES = {"bearish": -2, "slightly_bearish": -1, "neutral": 0,
          "slightly_bullish": 1, "bullish": 2}
COLORS = {"5m": "#f97316", "15m": "#eab308", "30m": "#22c55e",
          "1h": "#06b6d4", "4h": "#818cf8", "1d": "#e879f9", "1w": "#f43f5e"}


def chart_html(records):
    """SVG with actual timestamp spacing; missing grades break lines."""
    points = []
    for row in records:
        try:
            t = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            if t.tzinfo is None:
                continue
            points.append((t.timestamp(), row))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    points = sorted(points, key=lambda pair: pair[0])[-100:]
    if len(points) < 2 or points[-1][0] <= points[0][0]:
        return "<p>Grafiek ONTBREEKT — minimaal twee verschillende meettijden nodig.</p>"
    width, height, left, top = 940, 280, 65, 30
    plot_w, plot_h = 850, 210
    t0, t1 = points[0][0], points[-1][0]
    x = lambda t: left + (t - t0) / (t1 - t0) * plot_w
    y = lambda score: top + (2 - score) / 4 * plot_h
    parts = ['<svg viewBox="0 0 940 280" role="img" aria-label="Historische BTC signaalscores van min twee bearish tot plus twee bullish" style="width:100%;height:auto">']
    for score in range(-2, 3):
        yy = y(score)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="#44536d"/>')
        parts.append(f'<text x="10" y="{yy + 5:.1f}" fill="#cbd5e1" font-size="13">{score:+d}</text>')
    for tf in TIMEFRAMES:
        segments, current = [], []
        for t, row in points:
            signal = (row.get("signals") or {}).get(tf) or {}
            grade = signal.get("grade") if signal.get("status") == "ok" else None
            if grade not in SCORES:
                if current:
                    segments.append(current)
                    current = []
                continue
            current.append((x(t), y(SCORES[grade])))
        if current:
            segments.append(current)
        for segment in segments:
            if len(segment) > 1:
                coordinates = " ".join(f"{px:.1f},{py:.1f}" for px, py in segment)
                parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{COLORS[tf]}" stroke-width="2.5"/>')
            for px, py in segment:
                parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{COLORS[tf]}"/>')
    for stamp, px in ((points[0][0], left), (points[-1][0], left + plot_w)):
        label = datetime.fromtimestamp(stamp, timezone.utc).strftime("%d-%m %H:%M UTC")
        parts.append(f'<text x="{px:.1f}" y="270" fill="#cbd5e1" font-size="12" text-anchor="{"start" if px == left else "end"}">{label}</text>')
    parts.append("</svg>")
    legend = " ".join(f'<span style="color:{COLORS[tf]};margin-right:1rem">{tf.upper()}</span>' for tf in TIMEFRAMES)
    return "<h2>Signaaltrend (−2 bearish tot +2 bullish)</h2><p>Elke stip is een opgeslagen meting; ontbrekende scores worden niet doorgetrokken. Lijnen tonen geen koersverloop.</p><main>" + "".join(parts) + "<p>" + legend + "</p></main>"



def freshness_html(records):
    """Browser recomputes freshness on view; never claim build-time status is live."""
    valid = []
    for entry in records:
        try:
            stamp = datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is not None and isinstance(entry.get("signals"), dict):
                valid.append((stamp.astimezone(timezone.utc), entry))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    valid.sort(key=lambda pair: pair[0], reverse=True)
    if not valid:
        return '<section><h2>Datakwaliteit</h2><p>ONTBREEKT — geen geldige meting beschikbaar.</p></section>'
    stamp, entry = valid[0]
    stamp_text = html.escape(stamp.isoformat())
    status = []
    for tf in TIMEFRAMES:
        signal = entry["signals"].get(tf) or {}
        ok = signal.get("status") == "ok" and signal.get("grade") in LABELS
        status.append(f'<li>{tf.upper()}: {"beschikbaar" if ok else "ONTBREEKT"}</li>')
    return ('<section><h2>Datakwaliteit</h2><p id="freshness" data-updated="' +
            stamp_text + '">Controleren… (laatste meting: ' + stamp_text +
            ')</p><p>ACTUEEL ≤60 minuten; VEROUDERD >60 minuten. ' +
            'ONTBREEKT betekent dat geen geldige meting beschikbaar is.</p><ul>' +
            "".join(status) + '</ul></section>')


FRESHNESS_SCRIPT = """<script>
(function () {
  const el = document.getElementById("freshness");
  if (!el) return;
  function refresh() {
    const last = Date.parse(el.dataset.updated);
    const age = (Date.now() - last) / 60000;
    const state = !Number.isFinite(age) || age < -5 ? "ONTBREEKT — ongeldige tijd" :
      age > 60 ? "VEROUDERD" : "ACTUEEL";
    el.textContent = state + " — laatste meting " + el.dataset.updated +
      (Number.isFinite(age) ? " (" + Math.max(0, Math.floor(age)) + " minuten geleden)" : "");
  }
  refresh();
  setInterval(refresh, 60000);
})();
</script>"""



def collector_health_html(health):
    """Show persisted watchdog result separately from the snapshot freshness indicator."""
    if not isinstance(health, dict):
        return '<section><h2>Collectorbewaking</h2><p>ONTBREEKT — geen health-rapport beschikbaar.</p></section>'
    stamp = str(health.get("checked_at") or "")
    latest = str(health.get("last_snapshot_at") or "")
    status = health.get("status")
    if status not in ("current", "stale", "missing"):
        status = "missing"
    label = {"current": "ACTUEEL", "stale": "VEROUDERD", "missing": "ONTBREEKT"}[status]
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("naive timestamp")
        stamp = parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        stamp = ""
    if not stamp:
        return '<section><h2>Collectorbewaking</h2><p>ONTBREEKT — ongeldige controletijd.</p></section>'
    coverage = health.get("coverage_24h")
    coverage_html = '<p>24-uursdekking: ONTBREEKT — nog geen geldig dekkingsrapport.</p>'
    if isinstance(coverage, dict):
        observed = coverage.get("observed_snapshots")
        expected = coverage.get("expected_snapshots")
        gap = coverage.get("max_observed_gap_seconds")
        if (type(observed) is int and type(expected) is int and
                expected > 0 and 0 <= observed and
                (gap is None or (type(gap) is int and gap >= 0))):
            percentage = 100 * observed / expected
            gap_text = "ONTBREEKT" if gap is None else str(round(gap / 60)) + " minuten"
            coverage_html = ('<p>24-uursdekking: ' + str(observed) + '/' + str(expected) +
                             ' verwachte snapshots (' + f'{percentage:.1f}' +
                             '%). Grootste gemeten tussenruimte: ' + gap_text +
                             '.</p><p>Dit telt opgeslagen meetmomenten, niet complete candles. ' +
                             'De 24-uursdekking is een historisch rapport, geen live meting.</p>')
    return ('<section><h2>Collectorbewaking</h2><p id="collector-watchdog" data-checked="' +
            html.escape(stamp, quote=True) + '" data-status="' + status +
            '">Laatste watchdog-resultaat: ' + label + '</p><p>Laatste BTC-meting volgens watchdog: ' +
            html.escape(latest) + '</p>' + coverage_html + '<p>De onafhankelijke watchdog is niet continu; ' +
            'deze status kan verouderd zijn wanneer de controleworkflow niet draait.</p></section>')


WATCHDOG_SCRIPT = """<script>
(function () {
  const el = document.getElementById("collector-watchdog");
  if (!el) return;
  function refresh() {
    const age = (Date.now() - Date.parse(el.dataset.checked)) / 60000;
    const stale = !Number.isFinite(age) || age > 65 || age < -5;
    const labels = {current:"ACTUEEL", stale:"VEROUDERD", missing:"ONTBREEKT"};
    el.textContent = (stale ? "CONTROLE VEROUDERD" : labels[el.dataset.status] || "ONTBREEKT") +
      " — laatste watchdog-controle: " + el.dataset.checked;
  }
  refresh();
  setInterval(refresh, 60000);
})();
</script>"""


def render(records, health=None):
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
""" + collector_health_html(health) + freshness_html(records) + chart_html(records) + summary_html(records) + """<main><table><thead><tr><th>Meting (UTC)</th>""" + head + "</tr></thead><tbody>" + body + "</tbody></table></main>" + FRESHNESS_SCRIPT + WATCHDOG_SCRIPT + "</html>"


def build(source, output, health_source=None):
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
    health = None
    if health_source is not None:
        try:
            health = json.loads(Path(health_source).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(records, health), encoding="utf-8")


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
