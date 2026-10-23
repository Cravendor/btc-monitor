"""Read-only BTC signal history HTML with explicit missing-data states."""
import html
import json
from pathlib import Path
from scripts.signal_outcome_validation import evaluate_models, model_version
from scripts.signal_statistics import descriptive_confidence
from scripts.history_coverage import coverage, coverage_html, observations
from datetime import datetime, timezone, timedelta

TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d", "1w")
LABELS = {"bearish": "Bearish", "slightly_bearish": "Licht bearish",
          "neutral": "Neutraal", "slightly_bullish": "Licht bullish",
          "bullish": "Bullish"}



def summarize(records, hours):
    """Summarize observed snapshots only; no inference for missing intervals."""
    valid = observations(records)
    if not valid:
        return None
    end = valid[-1][0]
    start = end - timedelta(hours=hours)
    window = [(t, r) for t, r in valid if start < t <= end]
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
                      "neutral": observed.count("neutral"),
                      "unavailable": len(window) - len(observed)}
    return output


def summary_html(records):
    sections = []
    for label, hours in (("24 uur", 24), ("7 dagen", 168), ("30 dagen", 720)):
        valid = observations(records)
        report = coverage(records, valid[-1][0], hours) if valid else None
        stats = summarize(records, hours)
        if stats is None:
            sections.append("<h2>" + label + "</h2><p>ONTBREEKT — onvoldoende historische dekking.</p>")
            continue
        rows = []
        for tf, item in stats.items():
            rows.append("<tr><th>" + tf.upper() + "</th><td>" + str(item["observations"]) +
                        "</td><td>" + str(item["bullish"]) + "</td><td>" +
                        str(item["neutral"]) + "</td><td>" + str(item["bearish"]) +
                        "</td><td>" + str(item["changes"]) + "</td><td>" + str(item["unavailable"]) + "</td></tr>")
        sections.append("<h2>" + label + "</h2>" + coverage_html(report) + "<p>Gedeeltelijke geschiedenis wordt getoond. Aantallen geldige snapshots, geen tijdgewogen percentages. Deze beschrijvende telling kan meerdere modelversies bevatten; validatie staat hieronder per versie. Wissels kunnen over gaten heen lopen.</p>" +
                        "<div class=table-scroll role=region aria-label=Gegevens tabindex=0><table><tr><th>TF</th><th>Metingen</th><th>Bull</th><th>Neutraal</th><th>Bear</th><th>Wissels</th><th>Signaal ontbreekt</th></tr>" +
                        "".join(rows) + "</table></div>")
    return "".join(sections)



SCORES = {"bearish": -2, "slightly_bearish": -1, "neutral": 0,
          "slightly_bullish": 1, "bullish": 2}
COLORS = {"5m": "#f97316", "15m": "#eab308", "30m": "#22c55e",
          "1h": "#06b6d4", "4h": "#818cf8", "1d": "#e879f9", "1w": "#f43f5e"}


def chart_html(records):
    """SVG with actual timestamp spacing; missing grades break lines."""
    points = [(t.timestamp(), r) for t, r in observations(records)][-100:]
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
        previous = None
        previous_model = None
        for t, row in points:
            if previous is not None and t - previous > 2700 and current:
                segments.append(current)
                current = []
            previous = t
            signal = (row.get("signals") or {}).get(tf) or {}
            model = model_version(signal, row)
            if current and model != previous_model:
                segments.append(current)
                current = []
            previous_model = model
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
    return "<h2>Signaaltrend (−2 bearish tot +2 bullish)</h2><p>Elke stip is een opgeslagen meting; ontbrekende scores en meetgaten groter dan 45 minuten en modelwissels worden niet doorgetrokken. Lijnen tonen geen koersverloop.</p><div class=table-scroll role=region aria-label=Gegevens tabindex=0>" + "".join(parts) + "<p>" + legend + "</p></div>"



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
    coverage_text = coverage_html(health.get("coverage_24h"))
    return ('<section><h2>Collectorbewaking</h2><p id="collector-watchdog" data-checked="' +
            html.escape(stamp, quote=True) + '" data-status="' + status +
            '">Laatste watchdog-resultaat: ' + label + '</p><p>Laatste BTC-meting volgens watchdog: ' +
            html.escape(latest) + '</p><h3>24-uursdekking</h3>' + coverage_text + '<p>De onafhankelijke watchdog is niet continu; ' +
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


def outcome_tables(results):
    sections = []
    labels = {"bullish": "Bullish", "slightly_bullish": "Licht bullish",
              "bearish": "Bearish", "slightly_bearish": "Licht bearish"}
    for hours, by_tf in results.items():
        rows = []
        for tf, by_grade in by_tf.items():
            for grade, item in by_grade.items():
                total = item["evaluated"]
                rate = (f'{100 * item["confirmed_direction"] / total:.1f}%'
                        if total >= 10 else "ONVOLDOENDE DATA")
                confidence = descriptive_confidence(item["confirmed_direction"], total)
                bounds = confidence["interval"]
                ci = (f"{bounds[0] * 100:.1f}%–{bounds[1] * 100:.1f}%"
                      if bounds is not None else "ONVOLDOENDE DATA")
                rows.append('<tr data-tf="' + tf + '"><th>' + str(hours) + "u</th><td>" + tf.upper() +
                            "</td><td>" + labels[grade] + "</td><td>" + str(total) +
                            "</td><td>" + str(item["confirmed_direction"]) +
                            "</td><td>" + str(item["opposite_direction"]) +
                            "</td><td>" + str(item["candidate_signals"]) +
                            "</td><td>" + str(item["overlap_skipped"]) +
                            "</td><td>" + str(item["total_signals"]) +
                            "</td><td>" + str(item["missing_initial_price"]) +
                            "</td><td>" + str(item["awaiting_horizon"]) +
                            "</td><td>" + str(item["awaiting_price_window"]) +
                            "</td><td>" + str(item["missing_forward_price"]) +
                            "</td><td>" + str(item["unknown_observation_time"]) +
                            "</td><td>" + str(item["unsupported_horizon"]) +
                            "</td><td>" + str(item["excluded"]) + "</td><td>" + rate + "</td><td>" + ci + "</td></tr>")
        sections.append('<details class=validation-horizon data-horizon="' + str(hours) + '"><summary>Uitkomsten na ' + str(hours) +
                        ' uur</summary><div class=table-scroll role=region aria-label=Gegevens tabindex=0><table><tr><th>Horizon</th><th>TF</th>' +
                        '<th>Signaal</th><th>Beoordeeld</th><th>Richting juist</th>' +
                        '<th>Tegengesteld</th><th>Unieke kandidaten</th><th>Overgeslagen wegens overlap</th>' +
                        '<th>Geselecteerde signalen</th><th>Startkoers ontbreekt</th>' +
                        '<th>Horizon nog niet bereikt</th><th>Koersvenster nog open</th>' +
                        '<th>Vervolgkoers ontbreekt</th><th>Archieftijd onbekend</th>' +
                        '<th>Horizon niet meetbaar met dit TF</th><th>Uitgesloten</th>' +
                        '<th>Matchpercentage</th><th>95%-interval*</th></tr>' +
                        ''.join(rows) + '</table></div></details>')
    return ''.join(sections)


def validation_controls(models):
    choices = {
        "model": ("Modelversie", [(m, m) for m in models]),
        "tf": ("Timeframe", [(tf, tf.upper()) for tf in TIMEFRAMES]),
        "horizon": ("Horizon", [("1", "1 uur"), ("4", "4 uur"),
                                ("24", "24 uur"), ("168", "7 dagen")]),
        "sample": ("Telling", [("all_signals", "Alle unieke signalen"),
                              ("non_overlapping", "Zonder overlappende perioden")]),
    }
    controls = []
    for name, (label, options) in choices.items():
        items = '<option value="all">Alle</option>' + ''.join(
            '<option value="' + html.escape(value, quote=True) + '">' +
            html.escape(text) + '</option>' for value, text in options)
        controls.append('<label for="validation-' + name + '">' + label +
                        '<select id="validation-' + name + '" name="' + name + '">' +
                        items + '</select></label>')
    return ('<form id="validation-filters" hidden aria-label="Validatie filteren">' +
            ''.join(controls) + '<button type="button" id="validation-reset">Alle filters wissen</button>' +
            '<p id="validation-filter-status" role="status" aria-live="polite"></p></form>' +
            '<noscript><p>Filters vereisen JavaScript. Alle tabellen blijven hieronder beschikbaar.</p></noscript>')


VALIDATION_FILTER_SCRIPT = """<script>
(function () {
  const root = document.getElementById("signal-validation");
  const form = document.getElementById("validation-filters");
  if (!root || !form) return;
  const names = ["model", "tf", "horizon", "sample"];
  const fields = Object.fromEntries(names.map(name => [name, document.getElementById("validation-" + name)]));
  const params = new URLSearchParams(location.search);
  for (const name of names) {
    const value = params.get("v_" + name);
    if (value !== null && Array.from(fields[name].options).some(option => option.value === value)) {
      fields[name].value = value;
    }
  }
  function apply(save) {
    const selected = Object.fromEntries(names.map(name => [name, fields[name].value]));
    let count = 0;
    const focused = names.some(name => selected[name] !== "all");
    root.querySelectorAll(".validation-model").forEach(model => {
      model.hidden = selected.model !== "all" && selected.model !== model.dataset.model;
      model.querySelectorAll(".validation-sample").forEach(sample => {
        const policy = sample.dataset.sample === "all" ? "all_signals" : sample.dataset.sample;
        sample.hidden = selected.sample !== "all" && selected.sample !== policy;
        if (focused && !model.hidden && !sample.hidden) sample.open = true;
        sample.querySelectorAll(".validation-horizon").forEach(horizon => {
          horizon.hidden = selected.horizon !== "all" && selected.horizon !== horizon.dataset.horizon;
          if (focused && !horizon.hidden && !sample.hidden && !model.hidden) horizon.open = true;
          horizon.querySelectorAll("tr[data-tf]").forEach(row => {
            row.hidden = selected.tf !== "all" && selected.tf !== row.dataset.tf;
            if (!model.hidden && !sample.hidden && !horizon.hidden && !row.hidden) count++;
          });
        });
      });
    });
    document.getElementById("validation-filter-status").textContent = count +
      " validatieregels geselecteerd. Aantallen en percentages worden niet herberekend.";
    if (save) {
      try {
        const url = new URL(location.href);
        for (const name of names) {
          if (selected[name] === "all") url.searchParams.delete("v_" + name);
          else url.searchParams.set("v_" + name, selected[name]);
        }
        history.replaceState(null, "", url);
      } catch (_) { /* Filtering also works in local/read-only previews. */ }
    }
  }
  form.addEventListener("submit", event => event.preventDefault());
  for (const field of Object.values(fields)) field.addEventListener("change", () => apply(true));
  document.getElementById("validation-reset").addEventListener("click", () => {
    for (const field of Object.values(fields)) field.value = "all";
    apply(true);
  });
  form.hidden = false;
  apply(false);
})();
</script>"""


def outcome_html(records):
    results = evaluate_models(records)
    spaced = evaluate_models(records, sample_policy="non_overlapping")
    sections = [('<section class=validation-model data-model="' + html.escape(model, quote=True) + '"><h3>Modelversie: ' + html.escape(model) + '</h3>' +
                 '<details class=validation-sample data-sample=all><summary>Alle unieke signalen</summary>' +
                 outcome_tables(by_horizon) + '</details>' +
                 '<details class=validation-sample data-sample=non_overlapping><summary>Zonder overlappende evaluatieperioden</summary>' +
                 outcome_tables(spaced[model]) + '</details></section>')
                for model, by_horizon in results.items()]
    if not sections:
        sections = ['<p>ONVOLDOENDE DATA — geen identificeerbare modelversie met geldige signalen.</p>']
    return ('<section id=signal-validation><h2>Voorlopige signaalvalidatie (1u / 4u / 24u / 7d)</h2>' +
            validation_controls(results) +
            '<p>Filters veranderen alleen de weergave. Dit is beschrijvende validatie, geen bewijs van voorspellende waarde.</p>' +
            '<details><summary>Werkwijze en beperkingen</summary>' +
            '<p>Elke modelversie heeft afzonderlijke tabellen, aantallen en steekproefdrempels. '
            'De tweede telling selecteert per model en timeframe chronologisch het eerste '
            'directionele signaal, reserveert de volledige horizon plus 30 minuten, en kiest '
            'het volgende signaal pas strikt daarna. Selectie gebeurt vóór splitsing per '
            'signaalsterkte en zonder naar koersuitkomsten te kijken; ook signalen met '
            'ontbrekende prijzen of conflicten reserveren hun periode. Niet-geselecteerde '
            'signalen blijven als overlap zichtbaar en leveren nog wel waargenomen koersen. '
            'Niet-overlap maakt waarnemingen NIET onafhankelijk: autocorrelatie, regimes '
            'en selectiebias blijven mogelijk. Herstel van oudere signalen kan de selectie verschuiven. '
            'Drempels gelden opnieuw binnen elke telling. '
            'Versies worden niet samengevoegd tot een matchpercentage of interval. '
            'Koersen uit latere modelversies mogen als waargenomen vervolgprijs dienen; '
            'dit wijzigt het oorspronkelijke label niet. Een versieverschil is geen bewijs van verbetering. '
            'Een onbekende modelversie wordt niet aan de huidige versie toegewezen. '
            'Per timeframe en oorspronkelijke signaalsterkte. Eén signaal per afgesloten candle ' +
            'en bekende modelversie, met geldige candle-eindtijd en directioneel label; de toekomstige koers moet tussen de gekozen horizon en 30 minuten ' +
            'daarna zijn gemeten. Zonder geschikte koers blijft de uitkomst onbeoordeelbaar. ' +
            'De status gebruikt de laatste opgeslagen observatietijd, niet de huidige klok. '
            'Zonder startkoers: apart geteld. Horizon nog niet bereikt: wachten. '
            'Koersvenster nog open: de horizon is bereikt, maar de 30 minuten tolerantie lopen nog. '
            'Vervolgkoers ontbreekt: het hele venster is voorbij in het archief. '
            'Archieftijd onbekend: geen geldige observatietijd voor deze indeling. '
            'Horizon niet meetbaar: de volgende candle van dit timeframe sluit te laat; '
            'er wordt geen koers geïnterpoleerd. Conflicten en vlakke uitkomsten zijn uitgesloten. '
            'Een conflict telt bij elke betrokken oorspronkelijke signaalsterkte; tel die groepen niet op. '
            'Percentage pas vanaf 10 beoordeelde signalen. Dit is geen backtest en ' +
            'herhaalde of overlappende signalen zijn niet onafhankelijk. ' +
            'Het 95%-interval (Wilson) is uitsluitend beschrijvend, verschijnt vanaf 30 ' +
            'waarnemingen en corrigeert NIET voor overlap, selectie of autocorrelatie. ' +
            'Dit is geen bewijs van voorspellende waarde.</p></details>' + ''.join(sections) +
            '</section>' + VALIDATION_FILTER_SCRIPT)




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
        origin = "Hersteld bronsnapshot" if item.get("provenance", {}).get("kind") == "recovered_stored_signal" else "Live archief"
        versions = sorted({model_version(signal, item) for signal in (item.get("signals") or {}).values()
                           if isinstance(signal, dict) and model_version(signal, item)})
        version_text = html.escape(', '.join(versions) or "ONTBREEKT")
        rows.append("<tr><th>" + when + "</th><td>" + origin + "</td><td>" + version_text + "</td>" + "".join(cells) + "</tr>")
    head = "".join("<th>" + tf.upper() + "</th>" for tf in TIMEFRAMES)
    body = "".join(rows) if rows else '<tr><td colspan="10">Nog geen geldige historische metingen.</td></tr>'
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTC historische signaaltijdlijn</title>
<style>body{font:15px system-ui;background:#101827;color:#eef3ff;max-width:1200px;margin:2rem auto;padding:1rem}
.table-scroll{overflow-x:auto;max-width:100%;overscroll-behavior-x:contain;background:#1c2940;padding:1rem;border-radius:16px}
table{border-collapse:collapse;width:100%;white-space:nowrap}
td,th{padding:.65rem;text-align:left;border-bottom:1px solid #44536d}
.bull{color:#86efac}.bear{color:#fca5a5}.neutral{color:#cbd5e1}
p{color:#bac8da;overflow-wrap:anywhere}
*{box-sizing:border-box}h1{font-size:clamp(1.5rem,5vw,2rem)}
summary{cursor:pointer;padding:1rem;min-height:44px;background:#1c2940;border-radius:12px}
details{margin:.7rem 0}a{color:#93c5fd}
[hidden]{display:none!important}
#validation-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,12rem),1fr));gap:.8rem;background:#1c2940;padding:1rem;border-radius:12px}
#validation-filters label{display:grid;gap:.3rem;min-width:0}
#validation-filters select,#validation-filters button{font:inherit;min-width:0;max-width:100%;min-height:44px;background:#101827;color:#eef3ff;border:1px solid #64748b;border-radius:6px;padding:.5rem}
#validation-filter-status{grid-column:1/-1;margin:.3rem 0}
#validation-filters :focus-visible{outline:2px solid #93c5fd}
.table-scroll:focus-visible,summary:focus-visible{outline:2px solid #93c5fd}
@media(max-width:600px){body{margin:0 auto;padding:.8rem}.table-scroll{padding:.4rem}
td,th{padding:.6rem;font-size:.875rem}h2{font-size:1.25rem}svg{min-width:640px}}</style><h1>BTC — Historische signaaltijdlijn</h1>
<nav><a href="btc-timeframes.html">← Actuele timeframes</a></nav><p>Tabellen en grafiek: veeg horizontaal voor alle kolommen.</p>
<p>Laatste 100 opgeslagen snapshots, nieuwste bovenaan. Alle signalen zijn voorlopig;
dit is geen backtest. Tijdstempels zijn UTC. Ontbrekende gegevens blijven ONTBREEKT. Herstelde bronsnapshots bevatten uitsluitend destijds opgeslagen labels; de meettijd is de oorspronkelijke eindtijd van de snapshot. Historische prijzen en modeluitkomsten worden niet achteraf ingevuld.</p>
""" + collector_health_html(health) + freshness_html(records) + chart_html(records) + summary_html(records) + outcome_html(records) + """<div class=table-scroll role=region aria-label=Gegevens tabindex=0><table><thead><tr><th>Meting (UTC)</th><th>Herkomst</th><th>Modelversies</th>""" + head + "</tr></thead><tbody>" + body + "</tbody></table></div>" + FRESHNESS_SCRIPT + WATCHDOG_SCRIPT + "</html>"


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
