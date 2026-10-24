"""Mobile four-scenario cards with explicit provisional interpretation checks."""
from html import escape


def p(value):
    return format(value,',.1f').replace(',','_').replace('.',',').replace('_','.')+' USDT'


def pct(value):
    return 'ONTBREEKT' if value is None else format(value,'+.2f').replace('.',',')+'%'


def render(bundle):
    parts=['<section class="panel" style="margin-bottom:24px"><h2>Vier vooraf uitgewerkte routes</h2><p>Dagstructuur voor swing; weekstructuur voor langere posities. De tijdschaal is geen voorspelde aankomstdatum. Technische routes, psychologische hypothesen en Elliott-kandidaten blijven herkenbaar gescheiden.</p>']
    for mode,r in bundle['horizons'].items():
        attrs=' data-mode-panel="'+mode+'"'+(' hidden' if mode=='position' else '')
        expiry=escape(r.get('valid_until',''),quote=True)
        parts.append('<div'+attrs+'><h3>'+escape(r['label'])+'</h3>')
        if r['status']!='ready':
            parts.append('<p>ONVOLDOENDE DATA: '+escape(r['reason'])+'</p></div>')
            continue
        parts.append('<div class="swing-current" data-expires="'+expiry+'"><p class="state">'+
            ('Voorlopige technische voorkeur: '+escape(next(x['label'] for x in r['scenarios'] if x['id']==r['preferred_scenario'])) if r['preferred_scenario'] else 'Afwachten · geen duidelijke voorkeur')+
            '</p><p>Referentie '+(p(r['reference_price']) if r['reference_price'] else 'ONTBREEKT')+' · laatste slot '+p(r['last_close'])+
            ' · candle-einde <time>'+escape(r['candle_closed_at'])+'</time>.</p><p>Bronvenster vanaf <time>'+escape(r['history_from'])+'</time>; '+str(r['history_candles'])+
            ' aaneengesloten '+r['timeframe'].upper()+'-candles. Dit bewijst geen macrocyclusfase.</p><div class="four-routes">')
        for s in r['scenarios']:
            cards=[]
            for target in s['targets']:
                kind='Rangegrens' if target['kind']=='range_boundary' else 'ATR-projectie, geen Fib-doel'
                lower='; '.join(p(x['price'])+' ('+pct(x['change_pct'])+' vanaf deze testzone)' for x in target['rejection_to']) or 'geen lagere referentie beschikbaar'
                position=' · reeds voorbij de referentieprijs' if r['reference_price'] and (target['price']-r['reference_price'])*s['direction']<=0 else ''
                cards.append('<li><b>'+p(target['price'])+'</b> · '+pct(target['from_reference_pct'])+' vanaf referentie'+position+'<br><small>'+kind+'</small><br>Bij afwijzing mogelijke lagere referenties: '+lower+'</li>')
            parts.append('<article class="scenario route-'+s['id']+'"><h3>'+escape(s['label'])+'</h3><span class="tag">'+('Technisch ondersteund' if s['currently_supported'] else 'Voorwaardelijk')+'</span><p>'+escape(s['condition'])+'</p><ul>'+''.join(cards)+'</ul><p><b>Vervalt:</b> '+escape(s['invalidation_condition'])+'</p><details><summary>Fib-zones en interpretatie</summary>')
            parts.append('<p>'+(' · '.join(p(x['price'])+' ('+('retracement' if x['kind']=='fib_retracement' else 'extensie')+' '+format(x['ratio']*100,'.1f')+'%)' for x in s['fibonacci_ahead']) or 'Geen passende vooruitliggende Fib-niveaus bij deze ankers.')+'</p>')
            parts.append('<p>Fib-zones zijn mogelijke reactiegebieden. Een ATR-projectie is geen Fibonacci-doel. Onderbouwing komt uit dezelfde koersbron en telt niet dubbel.</p><p>Elliott: '+('prijspatroonkandidaten '+escape(', '.join(s['elliott_candidate_ids']))+' in dezelfde richting; geen bevestigde huidige golf.' if s['elliott_candidate_ids'] else 'geen passende getoetste prijspatroonkandidaat beschikbaar.')+'</p><p>Psychologische fase: niet automatisch vastgesteld. <a href="bias.html">Lees het gedateerde psychologische rapport</a> en vergelijk ankers, markt en timeframe.</p></details></article>')
        parts.append('</div><details><summary>Alle Fib- en rangezones: blijft het bull of bear?</summary><p>Reactie op de laatste afgesloten bevestigingscandle: '+escape(r['level_assessment']['confirmation_timeframe'].upper())+'; zone-ankers: '+escape(r['timeframe'].upper())+'. Niet geteste niveaus krijgen geen verzonnen beoordeling. De wijzer toont de geteste zone het dichtst bij de huidige prijs; hieronder blijven de andere reacties zichtbaar.</p><div style="overflow:auto"><table><thead><tr><th>Zone</th><th>Functie</th><th>Reactie</th><th>Volgende hoger</th><th>Volgende lager</th></tr></thead><tbody>')
        reactions={'closed_above':'Slot erboven','support_hold':'Steun gehouden','closed_below':'Slot eronder','rejection':'Afwijzing','undecided':'Onbeslist','not_tested':'Niet getest'}
        for x in r['level_assessment']['all_levels']:
            parts.append('<tr><td>'+p(x['price'])+'</td><td>'+escape(x.get('role',x['kind']))+'</td><td>'+reactions[x['reaction']]+'</td><td>'+(p(x['next_higher'])+'<br><small>'+escape(x['next_higher_role'])+'</small>' if x['next_higher'] else 'ONTBREEKT')+'</td><td>'+(p(x['next_lower'])+'<br><small>'+escape(x['next_lower_role'])+'</small>' if x['next_lower'] else 'ONTBREEKT')+'</td></tr>')
        parts.append('</tbody></table></div></details><details><summary>Kwaliteitscontrole, ankers en Elliott-regels</summary><p>Set-ID '+escape(r['scenario_set_id'])+' · '+escape(r['model_version'])+'. Geen kanspercentages.</p><ul>'+''.join('<li>'+escape(x['check'])+': '+escape(x['status'])+'</li>' for x in r['quality_checks'])+'</ul>')
        fib=r['fibonacci']
        if fib['status']=='calculated':
            parts.append('<p>Fib-ankers: '+p(fib['low'])+' (low-candle <time>'+escape(fib['low_at'])+'</time>) → '+p(fib['high'])+' (high-candle <time>'+escape(fib['high_at'])+'</time>). Richting '+escape(fib['direction'])+'; lineair; extremen van 20 eerdere candles. Geen bevestigde Elliott-ankers en geen exacte ticktijden.</p>')
            parts.append('<p>Retracement laag→hoog: H−r(H−L); hoog→laag: L+r(H−L). Tweepunts-extensie: L+q(H−L) omhoog of H−q(H−L) omlaag. 50% is halvering, geen Fibonacci-ratio.</p>')
        else:
            parts.append('<p>Fibonacci ONTBREEKT: volgorde van ankers niet vast te stellen.</p>')
        ew=r['elliott']
        parts.append('<p>'+escape(ew['reason'])+'</p>')
        for candidate in ew['candidates']:
            parts.append('<h4>'+escape(candidate['id'])+' · '+escape(candidate['direction'])+' · '+escape(candidate['status'])+'</h4><p>Ankers: '+ ' → '.join(p(x['price'])+' ('+escape(str(x['open_time_ms']))+' ms UTC)' for x in candidate['points'])+'</p><ul>'+''.join('<li><b>'+escape(c['rule'])+': '+escape(c['result'])+'</b> — '+escape(c['detail'])+'</li>' for c in candidate['checks'])+'</ul><p>'+escape(candidate['note'])+'</p>')
        parts.append('</details></div><p class="swing-expired" role="status" hidden>Deze scenarioroute is verlopen. Niveaus zijn verborgen; vernieuw de pagina.</p></div>')
    parts.append('<p>We volgen alle vier routes, niet achteraf alleen de passende. Een nieuwe route overschrijft eerdere analyses niet. Er worden geen posities of handelsadviezen gevolgd.</p></section>')
    return ''.join(parts)


CSS='''.four-routes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.four-routes ul{padding-left:18px}.four-routes li{margin-bottom:15px;overflow-wrap:anywhere}.route-very_bearish{border-top-color:#e88f96}.route-bearish{border-top-color:#dcad81}.route-bullish{border-top-color:#8bcbb7}.route-very_bullish{border-top-color:#55cda0}.mode-controls{max-width:640px;margin:0 auto 18px;display:flex;gap:10px}.mode-controls button{flex:1;min-height:44px}.mode-controls button[aria-pressed="true"]{border-color:var(--accent);color:var(--accent)}@media(max-width:780px){.four-routes{grid-template-columns:1fr}}'''
SCRIPT='''
function setMarketMode(mode){if(!['swing','position'].includes(mode))mode='swing';
document.querySelectorAll('[data-mode-panel]').forEach(el=>el.hidden=el.dataset.modePanel!==mode);
document.querySelectorAll('[data-select-mode]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.selectMode===mode)));
try{localStorage.setItem('btcMarketMode',mode);}catch(e){}
}
document.querySelectorAll('[data-select-mode]').forEach(el=>el.addEventListener('click',()=>setMarketMode(el.dataset.selectMode)));
try{setMarketMode(localStorage.getItem('btcMarketMode')||'swing');}catch(e){setMarketMode('swing');}
function expireRoutes(){document.querySelectorAll('.swing-current[data-expires]').forEach(el=>{
let expiry=Date.parse(el.dataset.expires);if(Number.isFinite(expiry)&&Date.now()>=expiry){el.hidden=true;el.nextElementSibling.hidden=false;}
});}expireRoutes();setInterval(expireRoutes,30000);
'''
