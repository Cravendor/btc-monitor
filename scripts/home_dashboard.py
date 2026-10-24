"""Public home page and conditional price scenarios; no collection or writes to data."""
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.market_scenarios import build_scenarios
from scripts.cycle_history import render_reference as render_cycle_history
from scripts import market_gauges, swing_dashboard, report_context, shb_dashboard
from scripts.swing_scenarios import build_swing_scenarios
from scripts.price_roadmap import build_roadmap
from scripts.roadmap_dashboard import render as render_roadmap


def escape(value):
    return html.escape(str(value), quote=True)


def price(value):
    # One decimal matches the source instrument's usual displayed precision.
    return format(value, ',.1f').replace(',', '_').replace('.', ',').replace('_', '.') + ' USDT'


def render(feed, as_of, ath=None, sentiment=None, context=None):
    result = build_scenarios(feed, as_of)
    swing_bundle = build_swing_scenarios(feed, as_of)
    ready = result['status'] == 'ready'
    interpretation = '<p>Fibonacci-niveaus wachten op geldige koersdata. Psychologische fasen en golftellingen worden niet ingevuld bij gebrek aan onderbouwing.</p>'
    content = '<p>Geen actuele, volledige 4H-berekening beschikbaar. Er worden geen oude niveaus als actueel getoond.</p>'
    freshness = '<span class="badge">ONVOLDOENDE DATA</span>'
    price_line = 'Prijsniveaus wachten op geldige data'
    if ready:
        r = result
        fib = r['fibonacci']
        fib_text = '<p>Geen Fibonacci-berekening: de volgorde van de range-extremen is niet vast te stellen.</p>'
        if fib['status'] == 'calculated':
            fib_rows = ''.join('<tr><td>' + format(x['ratio']*100, '.1f') + '%</td><td>' + price(x['price']) + '</td><td>' + escape(x['role']) + '</td></tr>' for x in fib['retracements'])
            extension = ' · '.join(format(x['ratio'], '.3f') + '×: ' + price(x['price']) for x in fib['extensions'] if x['ratio'] <= 1.618)
            distant = ' · '.join(format(x['ratio'], '.3f') + '×: ' + price(x['price']) for x in fib['extensions'] if x['ratio'] > 1.618)
            fib_text = ('<p>Geselecteerde referentiebeweging: ' + ('laag → hoog' if fib['direction'] == 'up' else 'hoog → laag') +
                        '. De uiteinden zijn de range-extremen van de 20 referentiecandles, geen bevestigde Elliott-golf.</p>' +
                        '<p>Low ' + price(fib['low']) + ' · ankercandle vanaf <time>' + escape(fib['low_at']) + '</time><br>High ' +
                        price(fib['high']) + ' · ankercandle vanaf <time>' + escape(fib['high_at']) + '</time>. De exacte ticktijd van het extremum is hiermee niet vastgesteld.</p>' +
                        '<div style="overflow:auto"><table><thead><tr><th>Terugname</th><th>Aandachtsniveau</th><th>Functie</th></tr></thead><tbody>' + fib_rows +
                        '</tbody></table></div><p>Tweepunts-extensies voorbij het eerdere extremum: ' + (extension or 'ONTBREEKT') +
                        '.</p><details><summary>Verdere extensies: 261,8% en 423,6%</summary><p>' +
                        (distant or 'Geen positieve projectieniveaus voor deze richting.') +
                        '.</p><p>Verdere extrapolaties, geen vastgestelde winstdoelen. Er is meer toekomstige prijsontwikkeling nodig om deze scenario’s te ondersteunen.</p></details>' +
                        '<p>Lineaire schaal. 50% is een gebruikelijk halveringsniveau, geen Fibonacci-ratio. Dit zijn berekende zones; een koersreactie is niet gegarandeerd.</p>')
        interpretation = ('<div id="interpretation-levels">' + fib_text + '</div><div class="context">' +
                          '<div><h3>Wall Street-psychologie</h3><p>Herstel: ongeloof → hoop → optimisme. Oververhitting: overtuiging → euforie. Terugval: complacency → angst → mogelijke capitulatie.</p>' +
                          '<p>Dit is een begrippenkader, geen vastgestelde huidige fase. De monitors toetsen fasehypothesen met argumenten vóór, tegen en ontbrekende sentimentgegevens.</p></div>' +
                          '<div><h3>Elliott Wave</h3><p>De monitors bespreken waar mogelijk een hoofdtelling en een alternatief, met ankerpunten, timeframe en ongeldigverklaring.</p>' +
                          '<p>Er is hier geen automatisch bevestigde golftelling. Zonder voldoende koersstructuur en subgolven blijft de telling voorlopig of ontbreekt zij.</p></div></div>' +
                          '<p><a href="bias.html">Lees de psychologische hypothesen en golftellingen in de oorspronkelijke monitorrapporten →</a>. Oudere rapporten worden niet achteraf aangevuld.</p>')
        states = {'bullish_breakout': 'Laatste 4H-slot boven de uitbraakdrempel',
                  'bearish_breakdown': 'Laatste 4H-slot onder de neerwaartse drempel',
                  'range': 'Laatste 4H-slot binnen de aandachtsrange'}
        freshness = '<span class="badge good">4H-berekening beschikbaar</span>'
        price_line = price(r['price']) if r['price'] is not None else 'Actuele futuresprijs ontbreekt'
        source = {'nas': 'NAS', 'github_fallback': 'GitHub-reserve', 'github_manual': 'GitHub handmatig',
                  'local': 'Lokaal'}.get(r['source'], 'Bron niet vastgelegd')
        cards = []
        for s in r['scenarios']:
            label = escape(s['label'])
            if s['id'] == 'range':
                body = ('<p class="condition">4H-slot tussen <b>' + price(s['lower']) + '</b> en <b>' +
                        price(s['upper']) + '</b>.</p><dl><dt>Aandachtspunt</dt><dd>Range-midden ' +
                        price(s['midpoint']) + '</dd><dt>Vervalt wanneer</dt><dd>Een 4H-candle buiten de drempels sluit.</dd></dl>' +
                        '<p>Geen bevestigde uitbraak. Wacht op een afsluiting buiten de range; een aanraking is geen bevestiging.</p>')
            else:
                bull = s['id'] == 'bullish_breakout'
                direction = 'boven' if bull else 'onder'
                reverse = 'onder' if bull else 'boven'
                body = ('<p class="condition">Eerst een 4H-slot ' + direction + ' <b>' + price(s['trigger']) +
                        '</b>.</p><dl><dt>Mogelijke vervolgniveaus</dt><dd>' + price(s['targets'][0]) +
                        '<br>' + price(s['targets'][1]) + '</dd><dt>Ontkracht bij</dt><dd>Een volgend 4H-slot ' +
                        reverse + ' ' + price(s['invalidation']) + '</dd></dl><p>Vervolgniveaus zijn volatiliteitsprojecties, geen voorspelde doelen. Controleer daarna of het niveau standhoudt.</p>')
            badge = '<span class="tag">Past bij laatste candle</span>' if s['confirmed_by_last_close'] else '<span class="tag muted">Voorwaardelijk</span>'
            cards.append('<article class="scenario ' + s['id'] + '"><h3>' + label + '</h3>' + badge + body + '</article>')
        delta_lines = []
        for key, label in (('spot', 'Spot'), ('usdt_futures', 'USDT-futures')):
            delta = r['provider_deltas'].get(key)
            delta_lines.append('<li>' + label + ': <b>' +
                               ((format(delta, ',.6f').rstrip('0').rstrip('.')) + ' BTC' if delta is not None
                                else 'ONTBREEKT voor dit venster') + '</b></li>')
        ratio = (format(r['volume_ratio'], '.2f') + '×') if r['volume_ratio'] is not None else 'ONTBREEKT'
        ratio24 = (format(r['volume_24h_ratio'], '.2f') + '×') if r['volume_24h_ratio'] is not None else 'ONTBREEKT'
        content = ('<div id="action-levels"><p class="state">' + states[r['state']] + '</p>' +
                   '<div class="levels"><div><small>Steun · laagste low van vorige 20 candles</small><strong>' + price(r['support']) +
                   '</strong></div><div><small>Weerstand · hoogste high van vorige 20 candles</small><strong>' + price(r['resistance']) +
                   '</strong></div></div><p>Beoordeelde candle: <time>' + escape(r['interval_start']) + '</time> tot <time>' +
                   escape(r['interval_end']) + '</time>. Slot: ' + price(r['last_close']) + '.</p>' +
                   '<div class="scenario-grid">' + ''.join(cards) + '</div>' +
                   '<div class="context"><div><h3>Volumebevestiging</h3><p>Laatste 4H-volume / gemiddelde van de 20 voorafgaande candles: <b>' +
                   ratio + '</b>.</p><p>Laatste 6 afgesloten 4H-candles / de 6 daarvoor (24H versus vorige 24H): <b>' +
                   ratio24 + '</b>.</p><p>Volume is context uit dezelfde futuresbron, geen onafhankelijke bevestiging van spotvraag.</p></div>' +
                   '<div><h3>Bitget buy−sell-delta</h3><ul>' + ''.join(delta_lines) +
                   '</ul><p>Alleen gecontroleerde dekking van hetzelfde 4H-venster. Agressorzijde niet onafhankelijk bevestigd.</p></div></div></div>' +
                   '<details><summary>Hoe zijn de niveaus berekend?</summary><p>Referentierange: ' + escape(r['range_start']) + ' tot ' +
                   escape(r['range_end']) + '. De 20 referentiecandles sluiten de beoordeelde candle uit.</p>' +
                   '<p>ATR14 = het gewone gemiddelde van 14 true ranges in de referentieperiode: max(high−low, |high−vorig slot|, |low−vorig slot|). ' +
                   'Dit is een eenvoudig gemiddelde, geen Wilder-ATR. ATR14: ' + price(r['atr14']) + '. Buffer: 0,1 × ATR14 = ' +
                   price(r['buffer']) + '. Bullish drempel = weerstand + buffer; bearish drempel = steun − buffer. ' +
                   'Vervolgniveaus liggen één en twee ATR vanaf de drempel. Ongeldigverklaring ligt aan de andere kant van de rangegrens met dezelfde buffer.</p>' +
                   '<p>Model: ' + escape(r['model_version']) + '. Niet historisch gekalibreerd; geen slagingspercentages. ' +
                   'Dit is een technische scenario-laag, niet de geïntegreerde vijfpuntsbeoordeling uit de monitors.</p></details>' +
                   '<p class="meta">Meting: <time>' + escape(r['snapshot_at']) + '</time> · ' + source +
                   ' · Bitget BTCUSDT USDT-FUTURES · niveaus in USDT, niet USD of euro.</p>')
    quote_expiry = result.get('valid_until', '')
    for route in swing_bundle['horizons'].values():
        if route.get('status') == 'ready' and route.get('reference_price') is not None:
            price_line = price(route['reference_price'])
            quote_expiry = route['valid_until']
            break
    expires = escape(result.get('valid_until', ''))
    return '''<!doctype html><html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>BTC Monitor — Overzicht en scenario’s</title>
<style>
:root{color-scheme:dark;--bg:#0c1320;--card:#162235;--line:#30415b;--text:#edf3fc;--muted:#a9b9d1;--accent:#f3b65d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,sans-serif}
main{max-width:1180px;margin:auto;padding:30px 24px 60px}a{color:#a9ccff}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:5px}
.eyebrow{color:var(--accent);font-size:.78rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase}h1{font-size:clamp(2rem,5vw,3.4rem);letter-spacing:-.04em;line-height:1.1;margin:.6em 0 .4em}h2{font-size:1.45rem;margin:0 0 .4rem}h3{font-size:1.1rem;margin:0 0 .7rem}p{color:var(--muted);margin:.7rem 0}strong,b{color:var(--text)}
.hero{display:flex;justify-content:space-between;align-items:center;gap:24px;margin:10px 0 28px}.quote{text-align:right}.quote strong{font-size:1.65rem;display:block}.quote small{color:var(--muted)}.badge{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:5px 12px;font-size:.8rem;margin-bottom:12px}.good{color:#9ee7c4}
table{width:100%;border-collapse:collapse}th,td{padding:8px;text-align:left;border-bottom:1px solid var(--line)}
.links,.scenario-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.links{margin-bottom:36px}.link-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px;color:var(--text);text-decoration:none;transition:border-color .15s}.link-card:hover{border-color:var(--accent)}.link-card span{color:var(--accent);font-size:.8rem}.link-card h2{font-size:1.15rem;margin-top:10px}.link-card p{font-size:.9rem;margin:8px 0 0}
.panel{border:1px solid var(--line);border-radius:20px;padding:26px;background:#101b2c}.state{color:var(--accent);font-weight:600}.levels{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}.levels>div{background:var(--card);border-radius:12px;padding:18px}.levels small{display:block;color:var(--muted)}.levels strong{display:block;font-size:1.5rem;margin-top:5px}.scenario{background:var(--card);border-top:3px solid #7893b6;border-radius:12px;padding:20px}.bullish_breakout{border-top-color:#83d5af}.bearish_breakdown{border-top-color:#e99a95}.tag{display:inline-block;font-size:.73rem;color:var(--accent);margin-bottom:10px}.muted{color:var(--muted)}.condition{min-height:70px}dt{color:var(--muted);font-size:.78rem}dd{margin:3px 0 14px;font-weight:600}.scenario p{font-size:.9rem}.context{display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:25px 0 15px}.context p,.context li{font-size:.9rem}.context ul{padding-left:18px}details{border-top:1px solid var(--line);padding:18px 0}summary{cursor:pointer;color:#bfd6f6}.meta{font-size:.8rem;overflow-wrap:anywhere}footer{margin-top:25px;font-size:.85rem}button{background:var(--card);border:1px solid var(--line);color:var(--text);padding:9px 16px;border-radius:10px;cursor:pointer}.hidden,[hidden]{display:none!important}
@media(max-width:780px){.links,.scenario-grid{grid-template-columns:1fr}.condition{min-height:0}.hero{display:block}.quote{text-align:left;margin-top:20px}.context,.levels{grid-template-columns:1fr}main{padding:20px 16px 40px}.panel{padding:18px}.link-card{padding:18px}}
''' + market_gauges.CSS + swing_dashboard.CSS + shb_dashboard.CSS + '''
</style></head><body><main>
<header class="hero"><div><div class="eyebrow">BTC Monitor / overzicht</div><h1>Eén plek voor je marktbeeld.</h1><p>Metingen, marktrichting en scenario’s met controleerbare prijsniveaus.</p></div>
<div class="quote" data-expires="''' + escape(quote_expiry) + '''"><small>Bitget futures · laatste momentopname</small><strong>''' + escape(price_line) + '''</strong></div></header>''' + market_gauges.render_all(feed, as_of, sentiment) + '''
''' + swing_dashboard.render(swing_bundle) + render_cycle_history(feed) + report_context.render(context) + '''
<nav class="links" aria-label="BTC-pagina’s">
<a class="link-card" href="btc-dashboard.html"><span>01 / METINGEN →</span><h2>Dashboard</h2><p>Prijs, funding, open interest, orderboek en gecontroleerde tradedelta.</p></a>
<a class="link-card" href="btc-timeframes.html"><span>02 / RICHTING →</span><h2>Multi-timeframe marktrichting</h2><p>Technische signalen van 5 minuten tot 1 week, met actualiteit per candle.</p></a>
<a class="link-card" href="btc-signal-history.html"><span>03 / HISTORIE →</span><h2>Historische signaaltijdlijn</h2><p>Opgeslagen modelsignalen en uitkomsten. Dit zijn geen gearchiveerde monitorrapporten.</p></a>
</nav><section class="panel" id="scenarios" data-valid-until="''' + expires + '''">
''' + freshness + '''<h2>4H-meetdetails voor extra timingcontext</h2><p>Drie voorwaardelijke 4H-scenario’s. Een intraperiode-prijsdoorbraak telt niet als bevestigd 4H-slot.</p>
<p id="stale-warning" role="status" hidden>Deze berekening is verouderd of er is een nieuw 4H-venster. Niveaus zijn verborgen. Vernieuw voor de laatste publicatie.</p>
''' + content + '''<button type="button" onclick="location.reload()">Vernieuwen</button></section>
''' + render_roadmap(build_roadmap(feed, as_of), ath) + '''
<section class="panel" style="margin-top:24px"><h2>Psychologie, Fibonacci en Elliott Wave</h2><p>Een interpretatielaag naast de meetgegevens. Fibonacci is een berekening; marktpsychologie en golftellingen zijn te toetsen hypothesen.</p><p><a class="badge" href="btc-methoden.html">Uitleg: Fibonacci, marktpsychologie en Elliott Wave →</a></p>''' + interpretation + '''</section>
<footer><p>De niveaus helpen bepalen wanneer je opnieuw kijkt. Het zijn geen koop-/verkooporders, stop-lossadvies of persoonlijke positiegrootte. Scenario’s kunnen mislukken; er worden geen kansen verzonnen.</p>
<p>Bron: <a href="https://github.com/Cravendor/btc-monitor/blob/main/data/latest.json">marktmetingen</a> · <a href="https://www.bitget.com/docs/catalog/classic-contract-market/classic-contract-market">Bitget-candledefinitie</a>. De NAS verzamelt elk halfuur; de werkelijke meettijd is leidend.</p>
<p>Technische signalen gebruiken koers, momentum en volume. Ze bepalen geen Wall Street-psychologiefase zoals euforie, angst of capitulatie.</p>
<p><a href="bias.html">Monitorrapporten en vijfpuntsbias →</a> — oorspronkelijke rapportteksten en expliciete beoordelingen. Dit archief is apart van de technische signaaltijdlijn; niet-gerapporteerde scores worden niet ingevuld.</p></footer>
</main><script>
function refreshFreshness(){
  const section=document.querySelector('#scenarios');
  const expiry=Date.parse(section.dataset.validUntil);
  if(!Number.isFinite(expiry))return;
  if(Date.now()>=expiry){
    const levels=document.querySelector('#action-levels');if(levels)levels.hidden=true;
    const interpretation=document.querySelector('#interpretation-levels');if(interpretation)interpretation.hidden=true;
    const roadmap=document.querySelector('#roadmap-levels');if(roadmap)roadmap.hidden=true;
    document.querySelector('#stale-warning').hidden=false;
    const badge=section.querySelector('.badge');badge.textContent='VEROUDERD';badge.classList.remove('good');
  }
}
function refreshAth(){const root=document.querySelector('#ath-reference');const expiry=Date.parse(root.dataset.validUntil);if(Number.isFinite(expiry)&&Date.now()>=expiry){const values=document.querySelector('#ath-values');if(values)values.hidden=true;const warning=document.querySelector('#ath-stale');if(warning)warning.hidden=false;}}
document.querySelectorAll('time').forEach(el=>{const value=Date.parse(el.textContent);if(Number.isFinite(value)){el.dateTime=el.textContent;el.textContent=new Date(value).toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam',timeZoneName:'short'});}});
function refreshQuote(){const q=document.querySelector('.quote');const t=Date.parse(q.dataset.expires);if(Number.isFinite(t)&&Date.now()>=t)q.querySelector('strong').textContent='Meting verouderd';}
refreshFreshness();refreshAth();refreshQuote();setInterval(()=>{refreshFreshness();refreshAth();refreshQuote();},60000);
''' + market_gauges.SCRIPT + swing_dashboard.SCRIPT + shb_dashboard.SCRIPT + '''
</script></body></html>'''


def build(feed_path, output, as_of=None, include_ath=False):
    as_of = as_of or datetime.now(timezone.utc).isoformat()
    feed = json.loads(Path(feed_path).read_text(encoding='utf-8'))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    ath = None
    if include_ath:
        from scripts.ath_reference import fetch_reference
        ath = fetch_reference(as_of)
        print('ATH reference:', ath['status'])
    from scripts.sentiment_reference import fetch_reference as fetch_sentiment
    sentiment = fetch_sentiment(as_of) if include_ath else None
    Path(output).write_text(render(feed, as_of, ath, sentiment, report_context.read_context(Path(feed_path).resolve().parent.parent, as_of)), encoding='utf-8')


if __name__ == '__main__':
    import sys
    build(sys.argv[1], sys.argv[2], include_ath='--ath' in sys.argv[3:])
