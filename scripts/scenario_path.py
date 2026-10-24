"""Price-ordered scenario milestones, not a dated forecast or execution history."""
from html import escape
import math


def build_path(route, scenario):
    quote=route.get('reference_price')
    if route.get('status')!='ready' or not isinstance(quote,(int,float)) or not math.isfinite(quote):
        return None
    direction=scenario['direction'];trigger=scenario['trigger_price']
    end=scenario['targets'][-1]['price'];buffer=route['buffer']
    grouped={}

    def add(value,label):
        key=round(value,8)
        item=grouped.setdefault(key,dict(price=value,labels=[]))
        if label not in item['labels']:
            item['labels'].append(label)

    fib=route.get('fibonacci',{})
    anchor_key='low' if direction>0 else 'high'
    origin=fib.get(anchor_key)
    if isinstance(origin,bool) or not isinstance(origin,(int,float)) or not math.isfinite(origin) or origin<=0:
        origin=None
    if origin is not None:
        anchor_name='swinglow' if direction>0 else 'swinghigh'
        anchor_time=fib.get(anchor_key+'_at')
        add(origin,'Beginprijs · '+anchor_name+' · '+route['timeframe'].upper()+
            (' · candle opent '+str(anchor_time) if anchor_time else ' · ankertijd ontbreekt'))
    add(trigger,'Bevestigingszone')
    levels=[dict(level,kind='fib_retracement') for level in fib.get('retracements',[])]
    levels+=scenario.get('fibonacci_ahead',[])
    start=origin if origin is not None else trigger
    for level in levels:
        if (level['price']-start)*direction>=0 and (end-level['price'])*direction>=0:
            kind='Fib-retracement' if level['kind']=='fib_retracement' else 'Fib-extensie'
            add(level['price'],kind+' '+format(level['ratio']*100,'.1f')+'%')
    for i,target in enumerate(scenario['targets']):
        add(target['price'],('Eerste doelzone' if i==0 else 'Verdere voorwaardelijke zone')+
            (' · rangegrens' if target['kind']=='range_boundary' else ' · ATR-projectie'))
    points=sorted(grouped.values(),key=lambda x:x['price']*direction)
    nearby=[p for p in points if abs(p['price']-quote)<=buffer]
    ahead=[p for p in points if (p['price']-quote)*direction>0]
    attention=min(nearby,key=lambda p:abs(p['price']-quote)) if nearby else (ahead[0] if ahead else None)
    invalidated=(route['last_close']-scenario['invalidation_price'])*direction<0
    live_boundary=(quote-scenario['invalidation_price'])*direction<0
    if invalidated:
        attention=None
    for point in points:
        point['state']=('attention' if point is attention else
                        'beyond' if (quote-point['price'])*direction>0 else 'ahead')
    return dict(points=points,quote=quote,direction=direction,attention=attention,origin=origin,
                near_attention=bool(nearby) and not invalidated,
                invalidated=invalidated,live_boundary=live_boundary,
                invalidation=scenario['invalidation_price'],buffer=buffer)


def render_path(route,scenario):
    from .shb_dashboard import price,condition
    path=build_path(route,scenario)
    if path is None:
        return ''
    esc=escape
    attention=path['attention']
    if path['invalidated']:
        status='Scenario ongeldig op broncandle-slot. Beoordeel een alternatieve route.'
    elif path['live_boundary']:
        status='Koers voorbij de ongeldigverklaringsgrens. Nu aandacht: controleer de slotbevestiging en alternatieve route.'
    elif attention:
        status=('Nu aandacht bij ' if path['near_attention'] else 'Volgende aandachtspunt bij ')+price(attention['price'])+'.'
    else:
        status='Koers voorbij alle getoonde zones. Opnieuw beoordelen; geen volgend doel afleiden.'
    items=[dict(p,kind='zone') for p in path['points']]
    items.append(dict(price=path['quote'],kind='now'))
    items.sort(key=lambda p:(p['price']*path['direction'],p['kind']!='now'))
    if path['origin'] is None:
        origin_note='Beginprijs ontbreekt: geen geldig swinganker beschikbaar.'
    elif route.get('fibonacci',{}).get('anchor_method')=='prior20_range_extremes':
        origin_note=('Beginprijs: high/low van de gekozen '+route['timeframe'].upper()+
                     '-range; geen vastgestelde all-time high of low. Historische ankerprijs, geen instapadvies.')
    else:
        origin_note='Beginprijs: swinganker uit de brondata; geen vastgestelde all-time high of low.'
    parts=['<section class="shb-levels scenario-path" aria-label="Scenariopad op prijsvolgorde">',
           '<h4>Waar staan we in dit scenario?</h4><p class="path-status" role="status">'+esc(status)+'</p>',
           '<p class="path-caption">'+('Omhoog' if path['direction']>0 else 'Omlaag')+
           ' op prijsvolgorde · geen voorspelde aankomstdatums</p>',
           '<p class="path-caption">'+esc(origin_note)+'</p><ol class="path-track">']
    for item in items:
        if item['kind']=='now':
            parts.append('<li class="path-now" aria-current="location"><span class="path-dot" aria-hidden="true"></span><strong>Huidige koers · '+price(item['price'])+'</strong><span>Bronmeting: <time>'+esc(route['recorded_at'])+'</time></span></li>')
            continue
        state=item['state']
        badge=('Nu aandacht' if path['near_attention'] else 'Volgende aandacht') if state=='attention' else ('Koers voorbij' if state=='beyond' else 'Voorwaardelijke zone')
        if path['invalidated']:
            badge='Route ongeldig · opnieuw beoordelen'
        parts.append('<li class="path-zone" data-path-state="'+state+'"><span class="path-dot" aria-hidden="true"></span><span class="path-badge">'+badge+'</span><strong>'+price(item['price'])+'</strong><span>'+esc(' / '.join(item['labels']))+'</span></li>')
    parts.append('</ol><p class="path-boundary">Ongeldigverklaringsgrens: '+price(path['invalidation'])+'. '+condition(scenario['invalidation_condition'])+'</p>')
    parts.append('<p class="path-check">Bij elke zone: BNB en SHB opnieuw bekijken; toets doorbraak, behoud of afwijzing met de afgesloten bevestigingscandle ('+esc(route['level_assessment']['confirmation_timeframe'].upper())+'). Dicht bij een zone betekent binnen de modelbuffer van '+price(path['buffer'])+'.</p>')
    parts.append('<p class="path-caption">Dit pad vergelijkt zones met de huidige koers. “Koers voorbij” bewijst geen eerdere aanraking of bevestigde doorbraak. De volgende zone is een aandachtspunt zodra de koers daar komt, geen zekerheid. Nieuwe metingen kunnen het pad wijzigen; er wordt geen gekozen route vastgezet of persoonlijke trade gevolgd.</p></section>')
    return ''.join(parts)


CSS='''
.scenario-path h4{margin:0 0 10px;font-size:.95rem}.scenario-path .path-status{color:var(--accent);font-weight:600}.scenario-path .path-caption{font-size:.72rem;color:var(--muted)}
.path-track{list-style:none;padding:0 0 0 10px;margin:20px 0}.path-track li{position:relative;border-left:2px solid var(--line);padding:0 0 22px 22px;min-width:0}.path-track li:last-child{padding-bottom:4px;border-left-color:transparent}.path-track li>span:not(.path-dot),.path-track strong{display:block;overflow-wrap:anywhere}.path-track strong{font-size:.9rem}.path-track li>span:not(.path-dot){font-size:.73rem;color:var(--muted)}
.path-dot{position:absolute;left:-6px;top:3px;width:10px;height:10px;border:2px solid var(--muted);border-radius:50%;background:var(--card)}.path-track .path-now .path-dot{background:var(--accent);border-color:var(--accent);box-shadow:0 0 0 4px #8bcbb724}.path-track .path-now strong{color:var(--accent)}.path-track [data-path-state="attention"] .path-dot{border-color:#ffcb88;background:#ffcb88}.path-track [data-path-state="attention"] .path-badge{color:#ffcb88}.path-track [data-path-state="beyond"] .path-dot{opacity:.5}.scenario-path .path-boundary,.scenario-path .path-check{font-size:.75rem;overflow-wrap:anywhere}.scenario-path .path-boundary{border-top:1px solid var(--line);padding-top:12px;color:#e8b3b5}
'''
