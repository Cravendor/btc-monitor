"""Two directional readings, 25 ordered combinations and auditable zone context.

BUY always means upward evidence, including in the bear route. Shared evidence
is disclosed. These are provisional ordinal rules, not probabilities or orders.
"""
from html import escape

VERSION = 'two_routes_zone_context_v1'
ANCHOR_VERSION = 'two_routes_zone_context_v2_anchors'
LABELS = {-2: 'Sterk SELL', -1: 'SELL', 0: 'Neutraal / afwachten', 1: 'BUY', 2: 'Sterk BUY'}


def combination(bull, bear):
    if bull is None or bear is None:
        return dict(id=None, status='unavailable', label='Onvoldoende data', score=None)
    if type(bull) is not int or type(bear) is not int or bull not in LABELS or bear not in LABELS:
        raise ValueError('unknown directional reading')
    if bull * bear < 0:
        label = 'Tegengestelde signalen · opnieuw beoordelen'
        score = 0
    elif bull == bear == 0:
        label = 'Geen duidelijke richting'
        score = 0
    else:
        total = bull + bear
        strength = 'Sterke ' if abs(total) == 4 else ''
        label = strength + ('opwaartse ' if total > 0 else 'neerwaartse ') + ('overeenstemming' if bull and bear else 'voorkeur · beperkte bevestiging')
        score = 2 if total == 4 else -2 if total == -4 else 1 if total > 0 else -1
    return dict(id=f'bull{bull:+d}_bear{bear:+d}', status='provisional', label=label, score=score)


def assess(route):
    missing = dict(model_version=VERSION, status='unavailable', routes=[],
                   combined=combination(None, None), context='Actuele brondata ontbreken.')
    if route.get('status') != 'ready' or route.get('reference_price') is None:
        return missing
    historical = route.get('route_anchors') or {}
    explicit_cycle = route.get('anchor_selection_policy')=='explicit_cycle'
    if explicit_cycle and historical.get('status')!='calculated':
        return dict(missing,context=historical.get('reason','Cyclusankers ontbreken.'))
    use_history = historical.get('status') == 'calculated'
    version = 'two_routes_cycle_zone_context_v3' if explicit_cycle else ANCHOR_VERSION if 'route_anchors' in route else VERSION
    fib = historical if use_history else (route.get('fibonacci') or {})
    if fib.get('status') != 'calculated':
        missing['context'] = 'Geen controleerbare high/low-ankers beschikbaar.'
        return missing
    price, close, buffer = route['reference_price'], route['last_close'], route['buffer']
    momentum = route['momentum']['score']
    assessment = route['level_assessment']
    bar = assessment['confirmation_bar']
    previous = assessment['confirmation_previous_close']
    # Each route has its own directionally measured ladder from the same anchors.
    # Endpoint is the opposing anchor; extension points remain conditional.
    low, high = fib['low'], fib['high']
    span = high - low
    results = []
    for key, direction, origin in [('bull', 1, low), ('bear', -1, high)]:
        levels = [dict(price=origin + direction*r*span, ratio=r,
                       kind='range_fraction' if r == .5 else 'fib_extension' if r > 1 else 'fib_progress')
                  for r in (0, .236, .382, .5, .618, .786, 1, 1.272, 1.618, 2.618)
                  if origin + direction*r*span > 0]
        nearest = min(levels, key=lambda x: abs(x['price']-price))
        zone = nearest['price']
        touched = bar['low'] <= zone+buffer and bar['high'] >= zone-buffer
        up = bar['close'] > zone+buffer
        down = bar['close'] < zone-buffer
        was_up = previous > zone+buffer
        was_down = previous < zone-buffer
        reaction = ('reclaim' if touched and was_down and up else
                    'breakdown' if touched and was_up and down else
                    'support_hold' if touched and was_up and up else
                    'rejection' if touched and was_down and down else
                    'undecided' if touched else 'not_tested')
        # Unconfirmed approach is neutral, even if broad momentum is strong.
        vote = 1 if reaction in ('reclaim', 'support_hold') else -1 if reaction in ('breakdown', 'rejection') else 0
        conflicts = bool(vote and (price-zone)*vote <= buffer)
        score = 0 if conflicts else vote
        if score and momentum*score > 0 and abs(momentum) == 2:
            score *= 2
        ahead = [x for x in levels if (x['price']-price)*direction > buffer]
        next_zone = nearest if abs(price-zone) <= buffer else (ahead[0] if ahead else None)
        # A retest requires an earlier close across this same zone and a new touch.
        prior = assessment.get('confirmation_prior_close')
        retest = bool(touched and prior is not None and
                      ((was_up and prior < zone-buffer) or (was_down and prior > zone+buffer)))
        results.append(dict(id=key, direction=direction, origin_price=origin,
            origin_at=fib['low_at' if direction > 0 else 'high_at'],
            anchor_method=fib['anchor_method'], levels=levels, selected_zone=zone,
            next_attention=next_zone, score=score, label=LABELS[score], reaction=reaction,
            retest_observed=retest, previous_side='above' if was_up else 'below' if was_down else 'buffer',
            current_conflicts=conflicts, momentum_score=momentum,
            invalidation_price=origin-direction*buffer,
            invalidated_on_native_close=(close-origin)*direction < -buffer,
            reason='Beoordeling van de dichtstbijzijnde routezone op afgesloten bevestigingscandle; sterke stand vereist ook sterk gelijkgericht momentum.'))
    combined = combination(results[0]['score'], results[1]['score'])
    tested = [x for x in results if x['reaction'] != 'not_tested']
    chosen = min(tested, key=lambda x: abs(x['selected_zone']-price)) if tested else None
    if chosen is None:
        context = 'Geen bevestigde reactie bij de huidige routezones. Wacht op een test; momentum alleen bevestigt geen volgende zone.'
    elif chosen['current_conflicts']:
        context = 'De actuele koers spreekt de gesloten zonereactie tegen. Nieuwe slotbevestiging nodig.'
    elif chosen['retest_observed'] and chosen['previous_side'] == 'below':
        context = ('Mogelijke terugtest van weerstand van onderaf. Afwijzing houdt de lagere route relevant; slot erboven en daarna behoud ondersteunen herstel.' if chosen['retest_observed'] else 'Weerstand vraagt om bevestiging.')
    elif chosen['retest_observed'] and chosen['previous_side'] == 'above':
        context = 'Mogelijke terugtest van steun van bovenaf. Behoud ondersteunt voortzetting; steunverlies maakt de lagere zone relevant.'
    elif chosen['reaction'] in ('reclaim', 'support_hold'):
        context = 'Opwaartse zonereactie; controleer behoud en de volgende weerstand. Een trendomslag is hiermee niet bevestigd.'
    elif chosen['reaction'] in ('breakdown', 'rejection'):
        context = 'Neerwaartse zonereactie; controleer de volgende steun en mogelijke uitputting. Geen automatische voortzetting.'
    else:
        context = 'Koers in de zonebuffer. Nog geen duidelijke doorbraak, afwijzing of steunbevestiging.'
    output = dict(model_version=version, status='provisional', routes=results, combined=combined,
        context=context, zone_price=chosen['selected_zone'] if chosen else None,
        confirmation_timeframe=assessment['confirmation_timeframe'],
        confirmation_closed_at=assessment['confirmation_closed_at'],
        source_family='bitget_price_volume', independent_evidence=False,
        news_status='not_integrated', news_reason='Nieuws wordt apart getoond; geen gevalideerde nieuwsscore in deze routebeoordeling.',
        anchor_scope='cycle_peaks_running_low' if explicit_cycle else 'available_history_high_then_later_low' if use_history else 'prior20_range_not_confirmed_cycle_ath_or_low',
        anchor_quality=historical if 'route_anchors' in route else None, position_tracked=False,
        probability=None)
    if 'route_anchors' not in route:
        output.pop('anchor_quality',None)
    return output


def render_meter(route, mode):
    from .market_gauges import svg
    from .shb_dashboard import price
    data = assess(route)
    esc = lambda x: escape(str(x), quote=True)
    parts = ['<article class="meter" id="shb-'+mode+'" data-expires="'+esc(route.get('valid_until',''))+'"><div class="meter-head"><h3>SHB · twee routes · vijf standen</h3><span class="data-badge" data-quality="'+('Beperkt' if data['status']=='provisional' else 'Ontbreekt')+'">Data: '+('beperkt' if data['status']=='provisional' else 'ontbreekt')+'</span></div>']
    if data['status'] == 'unavailable':
        return ''.join(parts)+'<p class="meter-reading">Onvoldoende data</p><p>'+esc(data['context'])+'</p></article>'
    parts.append('<div class="shb-levels"><h4>Gezamenlijke interpretatie</h4><p class="meter-reading">'+esc(data['combined']['label'])+'</p><p>'+esc(data['context'])+'</p>')
    historical=route.get('route_anchors') or {}
    for item in data['routes']:
        name = 'Bullroute' if item['id']=='bull' else 'Bearroute'
        parts.append('<details><summary>'+name+' · '+esc(item['label'])+'</summary>'+svg(item['score']/2,name+': '+item['label'])+'<div class="dial-labels"><span>Sterk SELL</span><span>Neutraal</span><span>Sterk BUY</span></div><p class="meter-reading">'+esc(item['label'])+'</p>')
        anchor_note=('Kandidaat-top en latere low uit '+str(historical.get('history_candles'))+' afgesloten '+route['timeframe'].upper()+'-candles; geen bewezen cyclus-ATH of definitieve bodem.' if data['anchor_scope']=='available_history_high_then_later_low' else 'High/low van 20 voorafgaande candles; cyclus-ATH/bodem nog niet bevestigd.')
        if data['anchor_scope']=='cycle_peaks_running_low':
            anchor_note='Cyclus '+str(historical['cycle_id'])+'; '+('bullbodem tussen cyclustoppen' if historical['phase']=='advance' else 'laagste low sinds de nieuwste cyclustop')+'; bear vanaf de hoogste gemeten cyclustop. Zelfde macroankers voor swing en positie.'
        parts.append('<p>Beginprijs '+price(item['origin_price'])+' · <time>'+esc(item['origin_at'])+'</time>. '+esc(anchor_note)+'</p><p>Zonecheck '+price(item['selected_zone'])+' · '+esc(item['reaction'])+'.</p><p>'+esc(item['reason'])+'</p>')
        if item['invalidated_on_native_close']:
            parts.append('<p>Route ongeldig op dag-/weekslot: opnieuw beoordelen.</p>')
        else:
            parts.append('<p>Volgende aandacht: '+(price(item['next_attention']['price']) if item['next_attention'] else 'voorbij getoonde zones; opnieuw beoordelen')+'.</p>')
        points=[dict(x,now=False) for x in item['levels']]+[dict(price=route['reference_price'],now=True)]
        points.sort(key=lambda x:x['price']*item['direction'])
        parts.append('<ol class="path-track">')
        for point in points:
            if point['now']:
                parts.append('<li class="path-now" aria-current="location"><strong>Huidige koers · '+price(point['price'])+'</strong></li>')
            else:
                attention=point['price']==(item['next_attention'] or {}).get('price')
                label='Beginprijs' if point['ratio']==0 else '50% · halvering' if point['ratio']==.5 else 'Fib '+format(point['ratio']*100,'.1f')+'%'
                parts.append('<li class="path-zone"><strong>'+price(point['price'])+'</strong><span>'+label+(' · Volgende aandacht' if attention else '')+'</span></li>')
        parts.append('</ol><p>Ongeldigverklaringsgrens: '+price(item['invalidation_price'])+' op '+esc(route['timeframe'].upper())+'-slot. Positie op dit pad bewijst geen eerdere activatie; geen aankomstdatums.</p></details>')
    if historical:
        if historical.get('anchor_version_id'):
            parts.append('<p>Ankerversie '+esc(historical['anchor_version_id'])+'</p>')
        parts.append('<p>Ankercontrole: '+esc(historical.get('reason',''))+'</p>')
        if historical.get('status')=='calculated':
            parts.append('<p>Historiedekking: '+esc(historical['history_from'])+' tot '+esc(historical['history_to'])+('. Alleen afgesloten dagcandles binnen het gekozen topinterval.' if data['anchor_scope']=='cycle_peaks_running_low' else '. De dag-/weekcandle voor bevestiging is uitgesloten van de ankerselectie.')+' Top aan begin bronvenster: '+('ja · eerdere toppen onbekend' if historical['high_at_history_boundary'] else 'nee')+'.</p>')
    parts.append('<details><summary>Uitleg en onderbouwing</summary><h4>25 combinaties en kwaliteitscontrole</h4><p>BUY betekent opwaartse ondersteuning; SELL neerwaartse ondersteuning, bij beide routes. Neutraal volgt uit geen bevestigde voorkeur, nooit uit ontbrekende data. Gedeelde brondata vormen geen dubbel onafhankelijk bewijs.</p><div style="overflow:auto"><table><caption>Rijen: bullroute · kolommen: bearroute</caption><thead><tr><th>Bull / Bear</th>'+''.join('<th>'+esc(LABELS[b])+'</th>' for b in LABELS)+'</tr></thead><tbody>')
    for bull in LABELS:
        parts.append('<tr><th>'+esc(LABELS[bull])+'</th>'+''.join('<td>'+esc(combination(bull,bear)['label'])+'</td>' for bear in LABELS)+'</tr>')
    parts.append('</tbody></table></div><p>Beide routes beoordelen hun eigen Fibonacci-ladder. Soms vallen zones samen en zijn de uitslagen gelijk. Niet alle 25 combinaties hoeven in de praktijk voor te komen.</p><p>'+esc(data['news_reason'])+' Geen vastgestelde Elliott-telling of psychologische fase. Geen persoonlijke TP-percentages of orders.</p></details></div><p class="meter-time">Bronmeting '+esc(route['recorded_at'])+' · zonereactie '+esc(data['confirmation_timeframe'])+' · slot '+esc(data['confirmation_closed_at'])+'</p><p class="model-tag">'+data['model_version']+' · voorlopig, niet gekalibreerd</p></article>')
    return ''.join(parts)
