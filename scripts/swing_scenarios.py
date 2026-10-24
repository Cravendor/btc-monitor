"""Versioned daily/weekly four-route scenarios and evidence checks.

No 4H dependency for swing/position readiness. No psychological phase guessed
from candles. No Elliott score or probabilities from provisional candidates.
"""
import hashlib
import json
from statistics import mean
try:
    from .market_scenarios import number, time_ms, iso, fibonacci_range
    from .native_timeframe_candles import PERIOD_MS, validate_rows
    from .multi_timeframe_signals import assess
    from .elliott_rules import assess_candidates
except ImportError:
    from market_scenarios import number, time_ms, iso, fibonacci_range
    from native_timeframe_candles import PERIOD_MS, validate_rows
    from multi_timeframe_signals import assess
    from elliott_rules import assess_candidates

MODEL = 'four_routes_daily_weekly_v1'
MODES = {'swing': ('1d', 'Swing · dagen tot weken'),
         'position': ('1w', 'Positietrade · weken tot maanden of langer')}
KINDS = ('very_bearish','bearish','bullish','very_bullish')
LABELS = dict(zip(KINDS, ('Sterk bearish','Bearish','Bullish','Sterk bullish')))


def valid_market(feed, as_of):
    m = feed['measurements'][0]
    if (m.get('exchange'), m.get('market'), m.get('symbol')) != ('bitget','USDT-FUTURES','BTCUSDT'):
        raise ValueError('wrong market')
    now = time_ms(as_of)
    start, finish = time_ms(m['started_at']), time_ms(m['finished_at'])
    if not 0 <= finish-start <= 3600000 or not -60000 <= now-start < 3600000 or finish>now+60000:
        raise ValueError('stale snapshot')
    return m


def native_rows(m, tf, as_of):
    metric = ((m.get('metrics') or {}).get('multi_timeframe') or {}).get('data',{}).get(tf) or {}
    now = time_ms(as_of)
    if metric.get('status')!='ok' or not -60000<=now-time_ms(metric.get('observed_at'))<3600000:
        raise ValueError('missing or stale native source')
    data = metric.get('data') or {}
    if data.get('interval','').lower()!=tf or data.get('closed_only') is not True:
        raise ValueError('wrong interval')
    rows = data['candles']
    if len(rows)>2000:
        raise ValueError('unexpected candle count')
    raw, seen = [], set()
    for c in rows:
        t = c.get('open_time_ms')
        if type(t) is not int or t < 0 or t in seen:
            raise ValueError('invalid/duplicate timestamp')
        seen.add(t)
        values = [number(c.get(k)) for k in ('open','high','low','close','base_volume_btc')]
        raw.append([t,*values,number(c.get('quote_volume_usdt',0))])
    checked = validate_rows(raw, tf, as_of)
    rows = checked['candles']
    # Retain the complete contiguous suffix; never bridge a historic gap for EW.
    start = 0
    for i in range(1,len(rows)):
        if rows[i]['open_time_ms']-rows[i-1]['open_time_ms']!=PERIOD_MS[tf]:
            start=i
    return rows[start:], metric['observed_at']


def current_price(m, as_of):
    metric = (m.get('metrics') or {}).get('futures_price') or {}
    try:
        d = metric.get('data') or {}
        p, ts = number(d.get('lastPr')), number(d.get('ts'))
        if metric.get('status')=='ok' and p>0 and -60000<=time_ms(as_of)-ts<3600000:
            return p
    except (TypeError, ValueError, OverflowError):
        pass
    return None


def route_set(rows, price, tf, mode, snapshot_at, observed, as_of, timing=None):
    prior, last = rows[-21:-1], rows[-1]
    low, high = min(c['low'] for c in prior), max(c['high'] for c in prior)
    tr = [max(c['high']-c['low'],abs(c['high']-p['close']),abs(c['low']-p['close']))
          for p,c in zip(prior[-15:-1],prior[-14:])]
    atr = mean(tr)
    if low>=high or atr<=0 or low-2.1*atr<=0:
        raise ValueError('unusable range/projections')
    mid, buffer = (low+high)/2, atr*.1
    signal = assess(rows,tf,as_of)
    if signal.get('status')!='provisional':
        raise ValueError('no momentum')
    avg_volume = mean(c['base_volume_btc'] for c in prior)
    volume = last['base_volume_btc']/avg_volume if avg_volume>0 else None
    fib = fibonacci_range([(c['open_time_ms'],c['open'],c['high'],c['low'],c['close'],c['base_volume_btc']) for c in prior])
    ew = assess_candidates(rows,tf)
    levels = [dict(price=low,kind='range_support',role='Low van vorige 20 candles'),
              dict(price=high,kind='range_resistance',role='High van vorige 20 candles')]
    if fib['status']=='calculated':
        levels += [dict(x,kind='fib_retracement') for x in fib['retracements']]
        levels += [dict(x,kind='fib_extension',role='Tweepunts-extensie; extrapolatie') for x in fib['extensions']]
    # Evaluate each actually tested zone separately; no automatic buy/sell action.
    unique_levels={round(x['price'],8):x for x in levels}
    tests=[]
    test_rows,timing_observed=timing if timing else (rows,observed)
    test_candle,test_previous=test_rows[-1],test_rows[-2]
    confirmation_tf='4h' if timing else tf
    for value,item in sorted(unique_levels.items()):
        if test_candle['low']<=value<=test_candle['high']:
            above=test_candle['close']>value+buffer
            below=test_candle['close']<value-buffer
            was_above=test_previous['close']>value+buffer
            was_below=test_previous['close']<value-buffer
            reaction=('closed_above' if was_below and above else
                      'closed_below' if was_above and below else
                      'rejection' if was_below and below else
                      'support_hold' if was_above and above else 'undecided')
            tests.append(dict(item,reaction=reaction,closed_at=iso(test_candle['open_time_ms']+PERIOD_MS[confirmation_tf])))
    selected=min(tests,key=lambda x:abs(x['price']-(price if price else last['close']))) if tests else None
    reaction=selected['reaction'] if selected else 'not_tested'
    vote=1 if reaction in ('closed_above','support_hold') else -1 if reaction in ('closed_below','rejection') else 0
    current_disagrees=bool(selected and price is not None and (price-selected['price'])*vote<0)
    if current_disagrees: vote=0
    level_assessment=dict(status='observed' if selected else 'awaiting_test',selected=selected,
                          tested_levels=tests,reaction=reaction,vote=vote,current_disagrees=current_disagrees,
                          zone_timeframe=tf,confirmation_timeframe=confirmation_tf,
                          confirmation_closed_at=iso(test_candle['open_time_ms']+PERIOD_MS[confirmation_tf]),
                          confirmation_source_at=timing_observed,
                          reason='Beoordeling op de laatste afgesloten broncandle; een huidige koers aan de andere kant maakt de uitkomst gemengd. Geen automatische voortzetting.')

    # Close rules are explicit and separate from hard intrabar Elliott constraints.
    definitions = [
        ('very_bearish',-1,low-buffer,low+buffer,[low-buffer-atr,low-buffer-2*atr]),
        ('bearish',-1,mid-buffer,mid+buffer,[low,low-buffer-atr]),
        ('bullish',1,mid+buffer,mid-buffer,[high,high+buffer+atr]),
        ('very_bullish',1,high+buffer,high-buffer,[high+buffer+atr,high+buffer+2*atr]),
    ]
    candidates=[]
    for key,direction,trigger,invalidation,targets in definitions:
        strong = key.startswith('very_')
        direction_ok = signal['score']*direction>0
        close_ok = (last['close']-trigger)*direction>0
        volume_ok = volume is not None and volume>=1.2
        supported = direction_ok and close_ok and (volume_ok or not strong)
        opposing = high+buffer if direction<0 else low-buffer
        # Fib levels are context, not mislabeled ATR targets or independent votes.
        fib_ahead = [dict(x,distance_pct=(x['price']/price-1)*100 if price else None)
                     for x in levels if x['kind'].startswith('fib_') and (x['price']-trigger)*direction>0]
        fib_ahead.sort(key=lambda x:x['price'],reverse=direction<0)
        next_levels=[]
        for j,t in enumerate(targets):
            target_type='range_boundary' if t in (low,high) else 'atr_projection'
            lower=sorted({x['price'] for x in levels if x['price']<t},reverse=True)[:2]
            next_levels.append(dict(price=t,kind=target_type,
                from_reference_pct=(t/price-1)*100 if price else None,
                rejection_to=[dict(price=p,change_pct=(p/t-1)*100,base_price=t) for p in lower]))
        c=dict(id=key,label=LABELS[key],direction=direction,
            condition=f'Afgesloten {tf.upper()}-slot '+('onder ' if direction<0 else 'boven ')+f'{trigger:.8f} USDT; momentum in dezelfde richting'+('; relatief volume ≥1,2×' if strong else '')+'.',
            trigger_price=trigger,invalidation_price=invalidation,
            invalidation_rule='later_closed_candle_above' if direction<0 else 'later_closed_candle_below',
            invalidation_condition=f'Een volgend {tf.upper()}-slot '+('boven ' if direction<0 else 'onder ')+f'{invalidation:.8f} USDT.',
            currently_supported=supported,targets=next_levels,fibonacci_ahead=fib_ahead[:4],
            source_family='bitget_price_volume',evidence=dict(close=close_ok,momentum=direction_ok,volume=volume_ok),
            elliott_candidate_ids=[x['id'] for x in ew['candidates'] if x['status']!='invalid' and x['direction']==('up' if direction>0 else 'down')],
            interpretation_status='technical_route_only_not_psychologically_confirmed',
            opposing_boundary=opposing)
        candidates.append(c)
    # Prefer the stronger condition only if it is actually supported; otherwise wait.
    active=next((x['id'] for x in reversed(candidates) if x['currently_supported'] and x['id']=='very_bullish'),None)
    if active is None:
        active=next((x['id'] for x in candidates if x['currently_supported']),None)
    level_roles={value:item.get('role',item['kind']) for value,item in unique_levels.items()}
    for scenario in candidates:
        for target in scenario['targets']:
            level_roles.setdefault(round(target['price'],8),'ATR-projectie' if target['kind']=='atr_projection' else 'Rangegrens')
    all_prices=sorted(level_roles)
    base=selected['price'] if selected else price
    level_assessment['next_higher']=[dict(price=x,role=level_roles[x],from_reference_pct=(x/price-1)*100 if price else None) for x in all_prices if base is not None and x>max(base,price if price else base)][:2]
    level_assessment['next_lower']=[dict(price=x,role=level_roles[x],from_zone_pct=(x/base-1)*100) for x in reversed(all_prices) if base is not None and x<base][:2]
    by_price={round(x['price'],8):x for x in tests}
    level_assessment['all_levels']=[dict(item,price=value,reaction=by_price.get(value,{}).get('reaction','not_tested'),next_higher=next((x for x in all_prices if x>value),None),next_lower=next((x for x in reversed(all_prices) if x<value),None),next_higher_role=next((level_roles[x] for x in all_prices if x>value),''),next_lower_role=next((level_roles[x] for x in reversed(all_prices) if x<value),'')) for value,item in sorted(unique_levels.items())]
    quality=[dict(check='market_identity',status='pass'),dict(check='native_closed_contiguous',status='pass'),
             dict(check='source_freshness',status='pass'),dict(check='fibonacci_anchor_order',status='pass' if fib['status']=='calculated' else 'unavailable'),
             dict(check='elliott_current_count',status='unavailable'),dict(check='psychological_phase',status='unavailable')]
    payload=dict(schema_version=1,model_version=MODEL,mode=mode,timeframe=tf,label=MODES[mode][1],status='ready',
        recorded_at=snapshot_at,source_observed_at=observed,reference_price=price,
        reference='bitget/BTCUSDT/USDT-FUTURES',unit='USDT',
        valid_until=iso(min(time_ms(snapshot_at)+3600000,time_ms(observed)+3600000,
                            last['open_time_ms']+2*PERIOD_MS[tf])),
        candle_closed_at=iso(last['open_time_ms']+PERIOD_MS[tf]),last_close=last['close'],
        history_from=iso(rows[0]['open_time_ms']),history_candles=len(rows),
        support=low,resistance=high,midpoint=mid,atr14=atr,buffer=buffer,
        momentum=signal,volume_ratio=volume,fibonacci=fib,elliott=ew,
        level_assessment=level_assessment,
        psychology=dict(status='unavailable',current_phase=None,report_url='bias.html',
            hypotheses=['Herstel / hoop / optimisme','Complacency / angst / verdere correctie'],
            reason='Fasehypothesen vergen het gedateerde psychologische rapport en passende onafhankelijke gegevens; geen automatische fase uit candles.'),
        scenarios=candidates,preferred_scenario=active,
        preference_reason='Voorlopige technische ondersteuning; geen onafhankelijke psychologie- of volledige Elliott-bevestiging.' if active else 'Afwachten: geen duidelijke combinatie van slot en momentum.',
        quality_checks=quality,data_quality='limited_interpretation',probability=None)
    identity=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)
    payload['scenario_set_id']=hashlib.sha256(identity.encode()).hexdigest()[:24]
    return payload


def build_swing_scenarios(feed,as_of):
    output={}
    for mode,(tf,label) in MODES.items():
        try:
            m=valid_market(feed,as_of)
            rows,observed=native_rows(m,tf,as_of)
            try:
                timing=native_rows(m,'4h',as_of)
            except (IndexError,KeyError,AttributeError,TypeError,ValueError,OverflowError):
                timing=None
            output[mode]=route_set(rows,current_price(m,as_of),tf,mode,m['finished_at'],observed,as_of,timing)
            output[mode]['valid_until']=iso(min(time_ms(output[mode]['valid_until']),time_ms(m['started_at'])+3600000,
                time_ms(timing[1])+3600000 if timing else time_ms(output[mode]['valid_until'])))
            output[mode].pop('scenario_set_id',None)
            output[mode]['scenario_set_id']=hashlib.sha256(json.dumps(output[mode],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
        except (IndexError,KeyError,AttributeError,TypeError,ValueError,OverflowError):
            output[mode]=dict(status='unavailable',mode=mode,timeframe=tf,label=label,scenarios=[],
                              reason='Onvoldoende actuele native dag-/weekdata; geen vervanging door 4H.',preferred_scenario=None)
    return dict(schema_version=1,model_version=MODEL,as_of=as_of,horizons=output)



def validate_frozen(route):
    if route.get('schema_version')!=1 or not route.get('model_version') or route.get('mode') not in MODES:
        raise ValueError('unknown scenario schema')
    if route.get('status')!='ready' or route.get('timeframe')!=MODES[route['mode']][0]:
        raise ValueError('unsupported horizon')
    data=dict(route);identifier=data.pop('scenario_set_id',None)
    digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()[:24]
    if identifier!=digest: raise ValueError('scenario content mismatch')
    if time_ms(route['candle_closed_at'])>time_ms(route['recorded_at']): raise ValueError('future source candle')
    if [s['id'] for s in route['scenarios']]!=list(KINDS): raise ValueError('four fixed routes required')
    for s in route['scenarios']:
        direction=s['direction']
        if direction not in (-1,1) or (number(s['trigger_price'])-number(s['invalidation_price']))*direction<=0:
            raise ValueError('invalid route geometry')
        for t in s['targets']:
            if number(t['price'])<=0 or (t['price']-s['trigger_price'])*direction<=0:
                raise ValueError('invalid target')
    return True
