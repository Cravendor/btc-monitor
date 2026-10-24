"""SHB linked visibly to a proposed scenario; no private trade inputs or orders."""
from html import escape
import re

CHOICES=(('auto','Automatisch voorstel'),('very_bearish','Sterk bearish'),('bearish','Bearish'),
         ('bullish','Bullish'),('very_bullish','Sterk bullish'))
VALUES={'SELL':-1,'HOLD':0,'BUY':1,'WAIT':0,None:None}


def price(value):
    return format(value,',.1f').replace(',','_').replace('.',',').replace('_','.')+' USDT'


def condition(text):
    return escape(re.sub(r'(?<![\w.])([0-9]+(?:\.[0-9]+)?) USDT',
                         lambda m:'≈ '+price(float(m[1])),text))


def gauge_action(route,choice='auto'):
    if route.get('status')!='ready' or route.get('reference_price') is None:
        return dict(action=None,reason='Onvoldoende actuele brondata; geen scenarioactie.',scenario_id=None)
    selected=route['preferred_scenario'] if choice=='auto' else choice
    assessment=(route.get('scenario_actions') or {}).get(selected)
    if assessment is not None:
        return assessment
    return dict(action='WAIT',reason='Er zijn vier voorgestelde routes, maar geen duidelijk ondersteunde voorkeur. Bekijk hun voorwaarden; geen BUY/SELL afdwingen.',scenario_id=None)


def render_meter(route,mode):
    from .market_gauges import svg
    title='SHB · '+('Swing · 1D' if mode=='swing' else 'Positie · 1W')
    available=route.get('status')=='ready' and route.get('reference_price') is not None
    quality='Beperkt' if available else 'Ontbreekt'
    expiry=escape(route.get('valid_until',''),quote=True)
    preferred=escape(route.get('preferred_scenario') or '',quote=True)
    parts=['<article class="meter" id="shb-'+mode+'" data-shb-mode="'+mode+'" data-preferred="'+preferred+'" data-expires="'+expiry+'">',
        '<div class="meter-head"><h3>'+title+'</h3><span class="data-badge" data-quality="'+quality+'">Data: '+quality.lower()+'</span></div>',
        '<label class="shb-selector">Voorgesteld scenario<select data-scenario-select="'+mode+'"'+(' disabled' if not available else '')+'>',
        ''.join('<option value="'+key+'">'+label+'</option>' for key,label in CHOICES),'</select></label>']
    for key,label in CHOICES:
        item=gauge_action(route,key)
        code=item['action'];reading=code if code is not None else 'Onvoldoende data'
        scenario_id=item.get('scenario_id')
        scenario=next((x for x in route.get('scenarios',[]) if x['id']==scenario_id),None)
        scenario_name=scenario['label'] if scenario else 'Geen duidelijke voorkeur'
        description='Automatisch voorstel: '+scenario_name if key=='auto' else scenario_name
        parts.append('<div class="shb-case" data-scenario-case="'+key+'"'+(' hidden' if key!='auto' else '')+'>'+svg(VALUES[code],title+': '+reading+' · '+description)+
            '<div class="dial-labels"><span>SELL</span><span>HOLD / WAIT</span><span>BUY</span></div>'+
            '<p class="meter-reading" role="status">'+reading+'</p><p class="shb-name">'+escape(description)+'</p>')
        if scenario and available:
            from .scenario_path import render_path
            parts.append(render_path(route,scenario))
            parts.append('<dl class="shb-levels"><dt>Bevestiging</dt><dd>'+condition(scenario['condition'])+'</dd><dt>Eerste zone → verdere getoonde route</dt><dd>'+price(scenario['targets'][0]['price'])+' ('+('rangegrens' if scenario['targets'][0]['kind']=='range_boundary' else 'ATR-projectie')+') → '+price(scenario['targets'][-1]['price'])+' ('+('rangegrens' if scenario['targets'][-1]['kind']=='range_boundary' else 'ATR-projectie')+')'+'</dd><dt>Tussenliggende Fib-aandachtszones</dt><dd>'+(' · '.join(price(x['price'])+' ('+('retracement' if x['kind']=='fib_retracement' else 'extensie')+' '+format(x['ratio']*100,'.1f')+'%)' for x in scenario['fibonacci_ahead']) or 'Geen passende niveaus bij deze ankers.')+'</dd><dt>Ongeldigverklaring</dt><dd>'+condition(scenario['invalidation_condition'])+'</dd></dl>')
        if scenario and available:
            parts.append('<p class="meter-time">Bron-slot '+escape(route['timeframe'].upper())+': <time>'+escape(route['candle_closed_at'])+'</time><br>Zonereactie '+escape(route['level_assessment']['confirmation_timeframe'].upper())+': <time>'+escape(route['level_assessment']['confirmation_closed_at'])+'</time>. Weergave afgerond; exacte grenzen staan in de brongegevens.</p>')
        parts.append('<details><summary>Uitleg en onderbouwing</summary><p class="meter-reason">'+escape(item['reason'])+'</p><p>BUY en SELL zijn technische actievoorwaarden binnen het getoonde scenario voor longblootstelling. Geen opdracht of uitgevoerde trade. HOLD betekent geen nieuwe scenarioactie; het bevestigt geen eigen positie of onaangeraakte stop-loss. WAIT betekent wachten op bevestiging of een passende route. Er worden geen persoonlijke trades gevolgd.</p><p>De voorwaarden zijn gebaseerd op het afgesloten broncandle-slot en actuele prijs. Een 4H-tegenreactie bij een doel kan aanleiding tot herbeoordeling geven; zij is niet hetzelfde als de dag-/weekslotregel voor ongeldigverklaring. Psychologie en Elliott blijven aanvullende hypotheses met hun eigen beperkingen.</p><p>De verdere getoonde route blijft voorwaardelijk. Bij iedere tussenliggende zone opnieuw toetsen; meters kunnen achterlopen bij een snelle omslag. Geen gegarandeerd doel of begrenzing van de markt.</p></details></div>')
    parts.append('<p class="meter-time">Altijd deze meting: <time>'+escape(route.get('recorded_at',''))+'</time>. Nieuwe metingen kunnen ankers en voorwaarden wijzigen; geen vergrendeld tradeplan.</p><p class="model-tag">Voorlopige scenarioregel · niet gekalibreerd</p></article>')
    return ''.join(parts)


CSS='''.shb-selector{display:block;font-size:.8rem;color:var(--muted);margin-top:12px}.shb-selector select{display:block;width:100%;max-width:100%;margin-top:5px;background:#0c1320;color:#edf3fc;border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit;min-height:44px}.shb-name{text-align:center;color:var(--accent)!important;font-weight:600}.shb-levels{border:1px solid var(--line);padding:12px;border-radius:12px;margin:12px 0}.shb-levels dd{font-size:.82rem;font-weight:400;overflow-wrap:anywhere}.shb-levels dt{font-size:.73rem}.scenario[data-selected="true"]{outline:2px solid var(--accent);outline-offset:2px}.scenario button{width:100%;min-height:44px;margin-bottom:12px}#shb-swing,#shb-position{scroll-margin-top:16px}'''

from .scenario_path import CSS as PATH_CSS
CSS+=PATH_CSS

SCRIPT='''
function selectScenario(mode,choice,scroll){
if(!['swing','position'].includes(mode))return;
const root=document.querySelector('[data-shb-mode="'+mode+'"]');if(!root)return;
const select=root.querySelector('[data-scenario-select]');
if(!Array.from(select.options).some(x=>x.value===choice))choice='auto';
select.value=choice;
root.querySelectorAll('[data-scenario-case]').forEach(el=>el.hidden=el.dataset.scenarioCase!==choice);
const selected=choice==='auto'?root.dataset.preferred:choice;
document.querySelectorAll('[data-route-mode="'+mode+'"]').forEach(el=>el.dataset.selected=String(el.dataset.routeId===selected));
try{localStorage.setItem('btcScenarioChoice_'+mode,choice);}catch(e){}
if(typeof refreshGauges==='function')refreshGauges();
if(scroll){if(typeof setMarketMode==='function')setMarketMode(mode);root.scrollIntoView({behavior:'smooth',block:'start'});}
}
document.querySelectorAll('[data-scenario-select]').forEach(el=>el.addEventListener('change',()=>selectScenario(el.dataset.scenarioSelect,el.value,false)));
document.querySelectorAll('[data-use-scenario]').forEach(el=>el.addEventListener('click',()=>selectScenario(el.dataset.useScenario,el.dataset.scenarioId,true)));
['swing','position'].forEach(mode=>{let choice='auto';try{choice=localStorage.getItem('btcScenarioChoice_'+mode)||'auto';}catch(e){}selectScenario(mode,choice,false);});
'''
