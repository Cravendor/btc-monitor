"""Conditional SHB states for proposed market scenarios, never position tracking.

SELL/BUY refer to price conditions for long exposure, not executed trades.
HOLD means no new scenario action. No personal stop/order/portfolio is inferred.
The furthest displayed route remains conditional at every intermediate zone.
"""
VERSION='scenario_shb_v1'


def assess_action(route, scenario):
    direction=scenario['direction']
    trigger=scenario['trigger_price']; invalidation=scenario['invalidation_price']
    target=scenario['targets'][0]['price']
    price=route['reference_price']; close=route['last_close']; previous=route['previous_close']
    bar=route['level_assessment']['confirmation_bar']; buffer=route['buffer']
    previously_beyond=(previous-trigger)*direction>0
    current_beyond=(close-trigger)*direction>0
    has_directional_evidence=previously_beyond or current_beyond
    invalidated=(close-invalidation)*direction<0
    current_conflicts=(price-trigger)*direction<=0 if price is not None else False
    target_tested=bar['high']>=target if direction>0 else bar['low']<=target
    counter_reaction=target_tested and (bar['close']-target)*direction < -buffer
    target_reached=price is not None and (price-target)*direction>=0
    zone=route['level_assessment'].get('selected')
    reaction=route['level_assessment']['reaction']
    intermediate=bool(zone and (zone['price']-trigger)*direction>0 and (target-zone['price'])*direction>0)
    zone_counter=bool(intermediate and price is not None and (price-zone['price'])*direction<0
                      and reaction in (('rejection','closed_below') if direction>0 else ('support_hold','closed_above')))
    zone_support=bool(intermediate and price is not None and direction>0 and price>zone['price']
                      and reaction in ('support_hold','closed_above'))
    action='WAIT';reason='De voorwaarden van dit scenario zijn nog niet bevestigd.'
    if price is None:
        action=None;reason='Actuele referentieprijs ontbreekt; geen SHB-wijzer.'
    elif invalidated:
        if direction>0 and previously_beyond:
            action='SELL';reason='De voorgaande broncandle stond boven de trigger; het nieuwste slot ligt voorbij de structuurgrens van deze huidige meting.'
        else:
            action='WAIT';reason='Dit scenario past nu niet: het broncandle-slot ligt voorbij zijn ongeldigverklaringsgrens. Bekijk het alternatief; geen automatische omgekeerde trade.'
    elif counter_reaction and has_directional_evidence:
        action='SELL' if direction>0 else 'HOLD'
        reason=('Afwijzing bij de eerste bovenliggende doelzone; afbouwconditie binnen deze bullish route.' if direction>0 else
                'Reactie omhoog bij de neerwaartse doelzone; eerst opnieuw beoordelen in plaats van automatisch verder bearish door te trekken.')
    elif zone_counter and has_directional_evidence:
        action='SELL' if direction>0 else 'HOLD'
        reason=('Tegenreactie bij een tussenliggende zone '+format(zone['price'],'.1f')+' USDT. '+
                ('Afbouwconditie binnen deze bullish route; verdere doelen opnieuw beoordelen.' if direction>0 else 'Herstel bij steun: de verdere bearish route eerst opnieuw beoordelen.'))
    elif current_conflicts:
        action='WAIT';reason='De actuele prijs bevestigt de afgesloten broncandle/trigger niet. Wacht op nieuwe bevestiging.'
    elif scenario['currently_supported']:
        if target_reached:
            action='HOLD';reason='De eerste getoonde doelzone is bereikt of gepasseerd. De verdere route is geen automatisme; beoordeel reactie of doorbraak opnieuw.'
        elif zone_support:
            action='BUY';reason='Steun/reclaim bij een tussenliggende zone is bevestigd en de bullish bronvoorwaarden blijven ondersteund; de eerste doelzone ligt nog hoger.'
        elif direction<0:
            action='SELL';reason='De bearish slot-/momentumvoorwaarden zijn bevestigd en de actuele prijs blijft onder de trigger. Dit is een afbouwconditie, geen opdracht of bewijs van een bestaande positie.'
        elif previous<=trigger:
            action='BUY';reason='Nieuwe bullish slotbevestiging boven de huidige trigger, passend momentum en actuele prijs boven die trigger; de eerste doelzone ligt nog hoger.'
        else:
            action='HOLD';reason='De bullish route blijft technisch ondersteund, maar er is geen nieuwe triggeroverschrijding of afwijzing. Geen nieuwe scenarioactie.'
    elif previously_beyond:
        action='HOLD';reason='De voorgaande broncandle stond voorbij de trigger en de oorspronkelijke grens van deze meting is op slotbasis nog niet overschreden; bevestiging is verzwakt. HOLD is geen bevestiging van jouw eigen positie of stop.'
    result=dict(model_version=VERSION,action=action,scenario_id=scenario['id'],scenario_label=scenario['label'],
        timeframe=route['timeframe'],trigger_price=trigger,invalidation_price=invalidation,
        targets=scenario['targets'],condition=scenario['condition'],invalidation_condition=scenario['invalidation_condition'],
        reason=reason,source_closed_at=route['candle_closed_at'],
        confirmation_timeframe=route['level_assessment']['confirmation_timeframe'],
        confirmation_closed_at=route['level_assessment']['confirmation_closed_at'],
        basis='current_snapshot_fixed_levels_not_a_tracked_trade',position_tracked=False,
        automatic_execution=False,hard_stop_verified=False,
        criteria=dict(previous_beyond_trigger=previously_beyond,current_beyond_trigger=current_beyond,
                      native_close_invalidated=invalidated,price_conflicts=current_conflicts,
                      counter_reaction_at_target=counter_reaction,target_reached=target_reached,
                      intermediate_counter_reaction=zone_counter,intermediate_support=zone_support))
    return result


def branches(route,scenario):
    direction=scenario['direction'];bar=route['level_assessment']['confirmation_bar']
    first,second=scenario['targets'][:2];trigger=scenario['trigger_price'];buffer=route['buffer']
    beyond=(bar['close']-first['price'])*direction>buffer
    touched=bar['high']>=first['price'] if direction>0 else bar['low']<=first['price']
    rejected=touched and (bar['close']-first['price'])*direction < -buffer
    retest=(bar['low']<=trigger+buffer and bar['high']>=trigger-buffer
            and (route['level_assessment']['confirmation_previous_close']-trigger)*direction>buffer)
    pause=abs(bar['close']-first['price'])<=buffer
    word='boven' if direction>0 else 'onder'
    return [
        dict(id='continuation',label='Doorbraak en voortzetting',
             condition=f'Afgesloten bevestigingscandle {word} de eerste zone {first["price"]:.8f} USDT, buiten de buffer; controleer daarna behoud.',
             observed=beyond,next_price=second['price'],next_kind=second['kind']),
        dict(id='retest',label='Terugtest van de triggerzone',
             condition=f'Test van {trigger:.8f} USDT; eerst controleren of het scenario daar standhoudt.',
             observed=retest,next_price=trigger,next_kind='trigger_retest'),
        dict(id='pause',label='Pauze bij de eerste zone',
             condition=f'Slot binnen de buffer rond {first["price"]:.8f} USDT: nog geen duidelijke doorbraak of afwijzing.',
             observed=pause,next_price=first['price'],next_kind=first['kind']),
        dict(id='counter_reaction',label='Afwijzing / tegenbeweging' if direction>0 else 'Steunreactie / herstel',
             condition=f'Test van {first["price"]:.8f} USDT en slot terug aan de andere kant buiten de buffer.',
             observed=rejected,next_price=None,next_kind='reassess_alternative',
             alternative_prices=first['rejection_to'] if direction>0 else [dict(price=x['price']) for x in route['level_assessment']['all_levels'] if x['price']>first['price']][:2]),
    ]


def attach(route):
    route['scenario_actions']={s['id']:assess_action(route,s) for s in route['scenarios']}
    for s in route['scenarios']:
        s['branches']=branches(route,s)
        s['furthest_displayed_price']=s['targets'][-1]['price']
        s['furthest_is_conditional']=True
    return route
