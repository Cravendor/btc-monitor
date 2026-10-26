"""Read-only top-down price charts. Candidates are not certified wave counts."""
from html import escape
from statistics import mean
from scripts.elliott_rules import assess_candidates, confirmed_pivots
from scripts.swing_scenarios import valid_market, native_rows, current_price
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS

TIMEFRAMES = ('1w', '1d', '4h', '1h')
MODEL = 'elliott_visual_linked_windows_v3'


def zones(rows, tf):
    """Fixed ATR band around confirmed pivots; descriptive, uncalibrated evidence.

    Only independent pivot events count. Candle touches within one event do not.
    Fib confluence is not another vote. Zones never generate wave endpoints.
    """
    tr = [max(c['high']-c['low'], abs(c['high']-p['close']),
              abs(c['low']-p['close'])) for p, c in zip(rows[-15:-1], rows[-14:])]
    width = mean(tr) * .15
    result = []
    for point in confirmed_pivots(rows):
        zone = next((z for z in result if z['kind'] == point['kind'] and
                     abs(z['anchor']-point['price']) <= width), None)
        if zone is None:
            zone = dict(anchor=point['price'], low=max(.00000001, point['price']-width),
                        high=point['price']+width, kind=point['kind'], pivots=[],
                        timeframe=tf)
            result.append(zone)
        zone['pivots'].append(point)
    for z in result:
        z['events'] = len(z['pivots'])
        z['evidence'] = 'herhaald pivotgebied' if z['events'] >= 2 else 'enkele pivot'
        # Current structural role, not an assertion that a future test will hold.
        z['role'] = ('steunreferentie' if rows[-1]['close'] > z['high'] else
                     'weerstandsreferentie' if rows[-1]['close'] < z['low'] else 'prijs in zone')
    return sorted(result, key=lambda z: z['anchor'])


def build(feed, as_of, history=None):
    out = dict(model_version=MODEL, status='unavailable', as_of=as_of,
               current_wave=None, nested_count='unproven', horizons=[])
    m = None
    try:
        m = feed['measurements'][0]
        observed = m['finished_at']
        # Validate original observation at its own time; never relabel it live.
        valid_market(feed, observed)
        age = time_ms(as_of)-time_ms(observed)
        if age < -60000:
            raise ValueError('future observation')
    except (KeyError, ValueError, IndexError, TypeError):
        if history is None:
            return out
        m = None
    fresh = m is not None and age < 3600000 and time_ms(as_of) < time_ms(m['started_at'])+3600000
    if history is not None:
        out.update(status='current' if all(history.get(tf,{}).get('status')=='complete' for tf in TIMEFRAMES) else 'partial',
                   observed_at=as_of, valid_until=iso(time_ms(as_of)//3600000*3600000+3600000),
                   history_mode=True)
    else:
        out.update(status='current' if fresh else 'historical', observed_at=observed,
                   valid_until=iso(time_ms(m['started_at'])+3600000))
    reference = None
    if history is not None and history.get('1h',{}).get('status')=='complete' and history['1h'].get('rows'):
        reference=history['1h']['rows'][-1]
    for tf in TIMEFRAMES:
        h = dict(timeframe=tf, status='unavailable', candidates=[], zones=[])
        try:
            if history is not None:
                source = history.get(tf,{})
                h['coverage'] = {k:v for k,v in source.items() if k != 'rows'}
                if source.get('status') not in ('complete','partial') or not source.get('rows'):
                    raise ValueError('requested long history incomplete')
                rows, source_at = source['rows'], source['source_at']
                if source.get('status')=='partial':
                    # Keep a checked contiguous historical prefix visible. Do
                    # not bridge a gap or advertise a complete current count.
                    gap=time_ms(source['first_missing_at'])
                    rows=[r for r in rows if r['open_time_ms']<gap]
                h['source_path'] = source['source_path']
            else:
                rows, source_at = native_rows(m, tf, observed)
            if len(rows) < 24:
                raise ValueError('insufficient contiguous source history')
            h.update(status='available', rows=rows, source_at=source_at,
                     closed_at=iso(rows[-1]['open_time_ms']+PERIOD_MS[tf]),
                     price=current_price(m, as_of) if fresh else reference['close'] if reference else None,
                     price_label='Snapshot' if fresh else ('1H-slot '+iso(reference['open_time_ms']+PERIOD_MS['1h'])[:16]+' UTC' if reference else None),
                     candidates=assess_candidates(rows, tf)['candidates'],
                     zones=zones(rows, tf))
        except (KeyError, ValueError, TypeError, OverflowError):
            pass
        out['horizons'].append(h)
    for h in out['horizons']:
        if h['status'] == 'available':
            pivots = confirmed_pivots(h['rows'])
            h['focus_start'] = pivots[-1]['open_time_ms'] if pivots else h['rows'][-min(32,len(h['rows']))]['open_time_ms']
            h['focus_origin'] = 'confirmed_pivot' if pivots else 'recent_window'
    # Link an exact, closed parent price window; never assert wave nesting.
    for parent, child in zip(out['horizons'], out['horizons'][1:]):
        if parent['status'] != 'available' or child['status'] != 'available':
            continue
        start = parent['focus_start']
        end = time_ms(parent['closed_at'])
        selected = [r for r in child['rows'] if start <= r['open_time_ms'] < end]
        expected = (end-start)//PERIOD_MS[child['timeframe']]
        if selected and len(selected) == expected and selected[0]['open_time_ms'] == start and selected[-1]['open_time_ms']+PERIOD_MS[child['timeframe']] == end:
            child['parent_window'] = dict(timeframe=parent['timeframe'],start=start,end=end)
    # Temporal containment is useful to inspect, but NOT proof of wave nesting.
    for parent, child in zip(out['horizons'], out['horizons'][1:]):
        for c in child['candidates']:
            c['parent_legs'] = []
            for p in parent['candidates']:
                for i, (a, b) in enumerate(zip(p['points'], p['points'][1:]), 1):
                    if a['open_time_ms'] <= c['points'][0]['open_time_ms'] and c['points'][-1]['open_time_ms'] <= b['open_time_ms']:
                        c['parent_legs'].append(dict(direction=p['direction'], leg=i,
                                                     parent_status=p['status']))
    return out


def price(v):
    return f'{v:,.1f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def chart(h, candidate, suffix, window=None):
    rows = h['rows']
    if window is not None:
        rows = [r for r in rows if window[0] <= r['open_time_ms'] < window[1]]
        if not rows:
            raise ValueError('empty chart window')
    points = candidate['points'] if candidate else []
    if window is None and h['timeframe'] in ('4h','1h') and len(rows)>400:
        # Only the drawing is zoomed. Candidate selection uses the full source.
        left=min(rows[-400]['open_time_ms'],points[0]['open_time_ms'] if points else rows[-400]['open_time_ms'])
        rows=[r for r in rows if r['open_time_ms']>=left]
    # Retain every candle, including intermediate wicks used by rule checks.
    start, end = rows[0]['open_time_ms'], rows[-1]['open_time_ms']+PERIOD_MS[h['timeframe']]
    lower = min(r['low'] for r in rows)
    upper = max(r['high'] for r in rows)
    if h['price'] is not None:
        lower, upper = min(lower,h['price']), max(upper,h['price'])
    pad = max((upper-lower)*.12,upper*.001)
    lower, upper = lower-pad, upper+pad
    x = lambda t: 70+(t-start)/(end-start)*760
    y = lambda p: 285-(p-lower)/(upper-lower)*250
    title = escape(h['timeframe'].upper()+' · '+suffix+' · Bitget BTCUSDT futures, USDT')
    parts = ['<svg class="ew-chart" viewBox="0 0 920 340" role="img" aria-labelledby="ew-'+h['timeframe']+'-'+suffix+'"><title id="ew-'+h['timeframe']+'-'+suffix+'">'+title+'</title>']
    for i in range(5):
        value = lower+(upper-lower)*i/4
        parts.append(f'<path d="M70 {y(value):.2f}H835" stroke="#314353"/><text x="842" y="{y(value)+4:.2f}">{price(value)}</text>')
    for z in h['zones']:
        color = '#63c8af' if z['role']=='steunreferentie' else '#e99b9d'
        parts.append(f'<rect x="70" y="{y(z["high"]):.2f}" width="760" height="{max(1,y(z["low"])-y(z["high"])):.2f}" fill="{color}" opacity=".10"/>')
    w = min(8,760/len(rows)*.65)
    for r in rows:
        xx=x(r['open_time_ms']+PERIOD_MS[h['timeframe']]/2)
        color='#69cfb4' if r['close']>=r['open'] else '#ed9199'
        parts.append(f'<path d="M{xx:.2f} {y(r["high"]):.2f}V{y(r["low"]):.2f}" stroke="{color}"/><rect x="{xx-w/2:.2f}" y="{min(y(r["open"]),y(r["close"])):.2f}" width="{w:.2f}" height="{max(1,abs(y(r["open"])-y(r["close"]))):.2f}" fill="{color}"/>')
    if points:
        color='#e5b56f' if candidate['status']=='invalid' else '#a8b9ff'
        coords=' '.join(f'{x(p["open_time_ms"]+PERIOD_MS[h["timeframe"]]/2):.2f},{y(p["price"]):.2f}' for p in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for i,p in enumerate(points):
            xx=x(p['open_time_ms']+PERIOD_MS[h['timeframe']]/2)
            yy=y(p['price'])
            label='start' if i==0 else str(i)+'?'
            parts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="3" fill="{color}"/><text x="{xx:.2f}" y="{yy+(19 if p["kind"]=="low" else -12):.2f}" text-anchor="middle">{label}</text>')
    last = rows[-1]
    if h.get('coverage') and h['timeframe'] in ('1w','1d'):
        top=max(rows,key=lambda r:r['high'])
        later=[r for r in rows if r['open_time_ms']>top['open_time_ms']]
        low=min(later,key=lambda r:r['low']) if later else None
        for r,value,label,dy in [(top,top['high'],'Top periode',-12)]+([(low,low['low'],'Low na top',35)] if low else []):
            xx=x(r['open_time_ms']+PERIOD_MS[h['timeframe']]/2)
            yy=y(value)
            parts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="5" fill="#f3b65d"/><text x="{xx:.2f}" y="{yy+dy:.2f}" text-anchor="middle">{label}</text>')
    # Last closed candle marker remains distinct from an optional fresh ticker.
    parts.append(f'<circle cx="{x(last["open_time_ms"]+PERIOD_MS[h["timeframe"]]/2):.2f}" cy="{y(last["close"]):.2f}" r="4" fill="white"/>')
    if h['price'] is not None:
        parts.append(f'<path d="M70 {y(h["price"]):.2f}H830" stroke="white" stroke-dasharray="4 5"/><text x="75" y="{y(h["price"])-6:.2f}">{escape(h.get("price_label") or "Snapshot")} · {price(h["price"])} USDT</text>')
    for t,anchor in ((start,'start'),((start+end)/2,'middle'),(end,'end')):
        parts.append(f'<text x="{x(t):.2f}" y="316" text-anchor="{anchor}">{iso(t)[:10]} {iso(t)[11:16]}</text>')
    parts.append('<text x="70" y="335">UTC · lineair · witte stip = laatste gesloten candle</text></svg>')
    return ''.join(parts)



def zoom_panel(h):
    rows=h['rows'];end=rows[-1]['open_time_ms']+PERIOD_MS[h['timeframe']]
    choices=[('Laatste beweging',h.get('focus_start',rows[-min(32,len(rows))]['open_time_ms']),end),
             ('Laatste 32 candles',rows[-min(32,len(rows))]['open_time_ms'],end),
             ('Laatste 96 candles',rows[-min(96,len(rows))]['open_time_ms'],end),
             ('Overzicht' if h['timeframe'] in ('1w','1d') else 'Overzicht · laatste 400 candles',rows[0 if h['timeframe'] in ('1w','1d') else -min(400,len(rows))]['open_time_ms'],end)]
    unique=[];seen=set()
    for label,a,b in choices:
        if (a,b) not in seen:
            seen.add((a,b));unique.append((label,a,b))
    # Count-based order makes +/- consistently narrow/widen the time window.
    unique.sort(key=lambda v:v[2]-v[1])
    default=next(i for i,v in enumerate(unique) if v[0]=='Laatste beweging')
    parts=['<div class="ew-zoom" data-tf="'+h['timeframe']+'"><h3>Laatste prijsbeweging · '+h['timeframe'].upper()+'</h3><p>Vanaf de laatste bevestigde pivot, waar beschikbaar. Het lopende eindpunt en Elliott-golfnummer zijn niet bevestigd. Meer detail is geen extra onafhankelijk bewijs.</p><div class="ew-zoom-controls"><button type="button" class="ew-zoom-in" aria-label="Inzoomen '+h['timeframe'].upper()+'">+ Inzoomen</button><label>Venster <select class="ew-zoom-select" aria-label="Grafiekvenster '+h['timeframe'].upper()+'">']
    for i,(label,a,b) in enumerate(unique):
        parts.append('<option value="'+str(i)+'"'+(' selected' if i==default else '')+'>'+label+'</option>')
    parts.append('</select></label><button type="button" class="ew-zoom-out" aria-label="Uitzoomen '+h['timeframe'].upper()+'">− Uitzoomen</button></div>')
    for i,(label,a,b) in enumerate(unique):
        visible=[r for r in rows if a<=r['open_time_ms']<b]
        parts.append('<div class="ew-zoom-view" data-view="'+str(i)+'"'+(' hidden' if i!=default else '')+'><p>'+label+' · '+str(len(visible))+' candles · '+escape(iso(a))+' tot '+escape(iso(b))+'.</p><div class="ew-chart-scroll">'+chart(h,None,'zoom-'+str(i),(a,b))+'</div></div>')
    parts.append('</div>')
    parent=h.get('parent_window')
    if parent:
        a,b=parent['start'],parent['end']
        linked=dict(h)
        if b<end:
            linked['price']=None
        parts.append('<details class="ew-parent-detail"><summary>Detail van de '+parent['timeframe'].upper()+'-beweging op '+h['timeframe'].upper()+'</summary><p>Exact hetzelfde gesloten tijdvenster: '+escape(iso(a))+' tot '+escape(iso(b))+'. Alleen tijd- en bronkoppeling; subgolftelling nog niet bewezen. De broncandles kunnen later herzien zijn.</p><div class="ew-chart-scroll">'+chart(linked,None,'parent',(a,b))+'</div></details>')
    elif h['timeframe']!='1w':
        parts.append('<p>Geen volledig controleerbaar hoger tijdvenster beschikbaar; geen bovenliggende telling ingevuld.</p>')
    return ''.join(parts)


def render(bundle):
    parts=['<section class="panel" id="elliott-scenarios"><h2>Elliott: van week naar uur</h2><p>Begin bij de grote structuur en zoom in. Bull en bear zijn mogelijke prijspatronen. Een steunzone helpt een draaipunt duiden; zij bewijst geen golfnummer of toekomstige afwijzing.</p>']
    if bundle['status']=='unavailable':
        return ''.join(parts)+'<p>Bron niet valideerbaar. Geen telling ingevuld.</p></section>'
    freshness = ('Volledige historie gecontroleerd' if bundle.get('history_mode') and bundle['status']=='current' else
                 'Historie wordt aangevuld; gedateerde delen zichtbaar, geen volledige actuele telling' if bundle.get('history_mode') else
                 'Bron actueel bij opbouw' if bundle['status']=='current' else 'HISTORISCH — bron verouderd, geen actuele telling')
    parts.append('<p class="ew-freshness" data-until="'+escape(bundle['valid_until'])+'">'+freshness+' · controle '+escape(bundle['observed_at'])+'.</p>')
    if bundle.get('history_mode'):
        parts.append('<p>Gewenste historie: <b>1 juli 2025 tot de laatste gesloten candle</b>. Voor UTC-weken begint de eerste week op 30 juni 2025. De zoomkeuze opent bij de laatste beweging. Kies Overzicht voor de volledige week-/dagreeks of de laatste 400 lagere candles. Historische telkandidaten lezen de volledige opgeslagen reeks. Een ontbrekende lange reeks wordt niet stilzwijgend vervangen door een korte snapshotreeks.</p>')
        parts.append('<p>Een gestippelde 1H-slotlijn is een apart referentiepunt uit de uurreeks, geen gesloten week-/dag-/4H-candle of live tick. De witte stip blijft het eigen laatste gesloten slot van elke timeframe.</p>')
    parts.append('<p><b>Huidige golf en samenhang tussen graden: nog niet bewezen.</b> De afzonderlijk uitklapbare historische tellingen tonen de twee recentste zes-pivotkandidaten, geselecteerd vóór de regeltoets. De zoomgrafieken tonen de koersbeweging zonder een golfnummer te verzinnen. Een ongeldige kandidaat blijft zichtbaar. Interne 5–3–5–3–5-opbouw is niet vastgesteld; het laatste label is geen claim over waar we nu zitten.</p>')
    for h in bundle['horizons']:
        tf=h['timeframe']
        parts.append('<details class="ew-timeframe"'+(' open' if tf=='1w' else '')+'><summary>'+tf.upper()+' · '+('Structurele zones' if tf in ('1w','1d') else 'Lokale zones')+'</summary>')
        if h['status']!='available':
            q=h.get('coverage',{})
            if q:
                parts.append('<p>Historiedekking: '+escape(str(q.get('candle_count',0)))+' / '+escape(str(q.get('required_candles','?')))+' gesloten candles. Ontbrekend: '+escape(str(q.get('missing_candles','onbekend')))+'.</p>')
                if q.get('status') == 'conflict':
                    check = q.get('cross_timeframe_check', {})
                    parts.append('<p><b>BRONCONFLICT:</b> De '+tf.upper()+'-candles komen niet overeen met de onderliggende '+escape(str(check.get('child', 'lagere timeframe'))).upper()+'-candles in prijs of BTC-volume. Volledige dekking betekent niet dat de bronvergelijking klopt.</p>')
                    if check.get('first_mismatch_at'):
                        parts.append('<p>Eerste afwijkende candle-opening UTC: '+escape(str(check['first_mismatch_at']))+'.</p>')
                    parts.append('<p>Grafieken voor deze timeframe geblokkeerd tot de broncontrole slaagt; geen lagere timeframe als vervanging.</p></details>')
                    continue
                if q.get('first_missing_at'):
                    parts.append('<p>Eerste ontbrekende candle-opening UTC: '+escape(str(q['first_missing_at']))+'.</p>')
            parts.append('<p>ONVOLDOENDE DATA voor deze timeframe; geen lagere timeframe als vervanging.</p></details>')
            continue
        parts.append('<p>'+str(len(h['rows']))+' gesloten candles · bron '+escape(h['source_at'])+' · laatste slot '+price(h['rows'][-1]['close'])+' USDT op '+escape(h['closed_at'])+'.</p>')
        if h.get('coverage',{}).get('status')!='complete' and bundle.get('history_mode'):
            q=h['coverage']
            parts.append('<p><b>ONVOLLEDIGE HISTORIE:</b> '+str(q.get('candle_count',0))+' / '+str(q.get('required_candles','?'))+' candles. Eerste gat '+escape(str(q.get('first_missing_at')))+'. Alleen het aaneengesloten beginstuk is getekend; geen telling door het ontbrekende deel heen.</p>')
        parts.append('<p>Bronreeks vanaf '+escape(iso(h['rows'][0]['open_time_ms']))+'. '+('Detailgrafiek: minimaal de laatste 400 candles en het volledige getekende kandidaatvenster.' if tf in ('4h','1h') and len(h['rows'])>400 else 'Volledige bronreeks afgebeeld.')+'</p>')
        if bundle.get('history_mode') and tf in ('1w','1d'):
            top=max(h['rows'],key=lambda r:r['high'])
            later=[r for r in h['rows'] if r['open_time_ms']>top['open_time_ms']]
            low=min(later,key=lambda r:r['low']) if later else None
            parts.append('<p>Grote prijsstructuur: hoogste high binnen deze bronperiode '+price(top['high'])+' USDT ('+escape(iso(top['open_time_ms']))+'); '+('laagste low op een latere candle '+price(low['low'])+' USDT ('+escape(iso(low['open_time_ms']))+').' if low else 'nog geen latere candle voor een low.')+' Dit zijn referentiepunten voor een grotere bull-/bearanalyse, geen automatisch bewezen golfnummers of lifetime-ATH.</p>')
        parts.append(zoom_panel(h))
        parts.append('<details class="ew-historical-counts"><summary>Historische telkandidaten · geen actuele scenarioselectie</summary>')
        for direction,label in (('up','Bull'),('down','Bear')):
            candidate=next((c for c in h['candidates'] if c['direction']==direction),None)
            parts.append('<h3>'+label+' · '+('ONGELDIGE standaardimpuls' if candidate and candidate['status']=='invalid' else 'voorlopige prijspatroonkandidaat' if candidate else 'geen zes-pivotkandidaat')+'</h3>')
            parts.append(chart(h,candidate,direction))
            if candidate:
                parts.append('<details><summary>Start, golfpunten en harde regels</summary><div class="ew-table"><table><thead><tr><th>Punt</th><th>Candle-opening UTC</th><th>USDT</th></tr></thead><tbody>')
                for i,p in enumerate(candidate['points']):
                    parts.append('<tr><td>'+('Start' if i==0 else str(i)+'?')+'</td><td>'+escape(iso(p['open_time_ms']))+'</td><td>'+price(p['price'])+'</td></tr>')
                parts.append('</tbody></table></div><p>Openingtijden van pivot-candles; geen exacte ticktijden. Startgrens '+price(candidate['invalidation_price'])+' USDT hoort bij deze historische kandidaat, niet bij een veronderstelde volgende golf.</p><ul>')
                parts.extend('<li>'+escape(c['rule'])+': <b>'+escape(c['result'])+'</b> — '+escape(c['detail'])+'</li>' for c in candidate['checks'])
                parts.append('</ul><p>Harde overlapregels gelden intrabar, inclusief wicks. Een slot kan een schending niet ongedaan maken.</p>')
                a,b=candidate['points'][-2:]
                distance=abs(b['price']-a['price'])
                fibs=[(r,b['price']-r*distance if b['price']>a['price'] else b['price']+r*distance) for r in (.236,.382,.5,.618,.786)]
                parts.append('<p>Fib-context bij het laatste getekende been 4? → 5?: '+price(a['price'])+' → '+price(b['price'])+' USDT. Lineaire terugname vanaf het eindpunt: '+ '; '.join(f'{r*100:g}%: '+price(v) for r,v in fibs)+'. 50% is halvering, geen Fibonacci-ratio. Bij een ongeldige telling blijft dit alleen rekenkundige context bij deze prijsbeweging; geen steunbewijs of koersdoel.</p>')
                if tf!='1w':
                    links=candidate.get('parent_legs',[])
                    parts.append('<p>'+('Tijdvenster past binnen bovenliggend been: '+escape('; '.join(x['direction']+' '+str(x['leg'])+' ('+x['parent_status']+')' for x in links))+'. Alleen tijdsoverlap; interne golfstructuur niet bewezen.' if links else 'Geen volledig omvattend bovenliggend kandidaatbeen gevonden. Deze lokale kandidaat bewijst de hogere telling niet.')+'</p>')
                parts.append('</details>')
        parts.append('</details>')
        parts.append('<details><summary>Prijstijdlijn: steun, weerstand en bewijs</summary><p>Van laag naar hoog, geen voorspelde aankomstdata. Bandbreedte: ±0,15 × ATR(14) rond de eerste pivot. Herhaalde pivotgebieden hebben meer waargenomen reacties dan een enkele pivot; dit is geen gekalibreerde steunkracht of kans op rejection. Een Fib-ratio uit dezelfde koersdata is geen extra onafhankelijke bevestiging.</p><div class="ew-table"><table><thead><tr><th>Zone USDT</th><th>Rol bij laatste slot</th><th>Bewijs op '+tf.upper()+'</th></tr></thead><tbody>')
        for z in h['zones']:
            parts.append('<tr><td>'+price(z['low'])+'–'+price(z['high'])+'</td><td>'+escape(z['role'])+'</td><td>'+escape(z['evidence'])+' · '+str(z['events'])+' bevestigde pivot(s)</td></tr>')
        parts.append('</tbody></table></div><p>Een slot buiten een zone op '+tf.upper()+' verandert de lokale prijsinterpretatie. Alleen een overtreden golfregel ontkracht de betreffende Elliott-kandidaat; een lokale steunbreuk ontkracht niet automatisch de weektelling.</p></details></details>')
    parts.append('<p>Bron: opgeslagen native Bitget BTCUSDT USDT-FUTURES-candles, USDT. Geen lifetime-ATH uit dit beperkte venster afgeleid. Geen kanspercentages of verplichte koersroute. <a href="bias.html">Lees de onderbouwde rapportinterpretatie</a>.</p></section>')
    return ''.join(parts)


CSS = '''.ew-chart{display:block;width:100%;height:auto;background:#10202e;border-radius:10px;margin:12px 0}.ew-chart text{fill:#e7edf4;font-size:12px;font-family:system-ui,sans-serif}.ew-timeframe{border-top:1px solid #415465;padding:14px 0}.ew-table{overflow:auto}.ew-table td,.ew-table th{white-space:nowrap}.ew-freshness{padding:10px;border-left:3px solid #e5b56f}@media(max-width:600px){.ew-chart{min-width:680px}.ew-timeframe{overflow-x:auto}}'''
SCRIPT = '''document.querySelectorAll('.ew-freshness').forEach(el=>{function check(){if(Date.now()>=Date.parse(el.dataset.until))el.textContent='HISTORISCH — bron verouderd; grafieken tonen de gedateerde observatie, geen actuele telling.';}check();setInterval(check,60000);});'''

CSS += '.ew-zoom-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.ew-zoom-controls button,.ew-zoom-controls select{font:inherit;padding:8px;border-radius:6px}.ew-chart-scroll{overflow-x:auto;max-width:100%}.ew-zoom-view[hidden]{display:none}'
SCRIPT += """document.querySelectorAll('.ew-zoom').forEach(root=>{const select=root.querySelector('select');const plus=root.querySelector('.ew-zoom-in');const minus=root.querySelector('.ew-zoom-out');function show(){root.querySelectorAll('.ew-zoom-view').forEach(el=>{el.hidden=el.dataset.view!==select.value;});plus.disabled=select.selectedIndex===0;minus.disabled=select.selectedIndex===select.options.length-1;}select.addEventListener('change',show);plus.addEventListener('click',()=>{if(select.selectedIndex>0)select.selectedIndex--;show();});minus.addEventListener('click',()=>{if(select.selectedIndex<select.options.length-1)select.selectedIndex++;show();});show();});"""
