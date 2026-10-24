"""Forward review of ALL frozen scenario routes and level reactions.

One first-published scenario set per source candle/model/mode. No replay of old
candles into predictions; no 'winning' selection of just the preferred route.
Closed-candle barriers are descriptive and not exchange executions.
"""
import json
from bisect import bisect_right
from datetime import datetime,timezone
from pathlib import Path
from html import escape
try:
    from .market_scenarios import time_ms, number, iso
    from .swing_scenarios import build_swing_scenarios,MODES,validate_frozen
    from .native_timeframe_candles import PERIOD_MS
except ImportError:
    from market_scenarios import time_ms, number, iso
    from swing_scenarios import build_swing_scenarios,MODES,validate_frozen
    from native_timeframe_candles import PERIOD_MS

DAYS=(7,30,90)


def read_records(root,as_of):
    output=[]
    for path in sorted(Path(root).glob('????/??/??/*.json')):
        try:
            r=json.loads(path.read_text(encoding='utf-8'))
            if time_ms(r['finished_at'])>time_ms(as_of): continue
            if (r.get('exchange'),r.get('market'),r.get('symbol'))!=('bitget','USDT-FUTURES','BTCUSDT'): continue
            output.append((r,str(path.relative_to(root))))
        except (OSError,ValueError,TypeError,KeyError,OverflowError):
            continue
    return sorted(output,key=lambda x:time_ms(x[0]['finished_at']))


def evaluate(records,as_of,days=30):
    if days not in DAYS: raise ValueError('unsupported horizon')
    now=time_ms(as_of)
    samples={}; paths={mode:{} for mode in MODES}
    for record,path in records:
        if time_ms(record['finished_at'])>now: continue
        bundle=record.get('scenario_snapshot') or {}
        # Require contemporaneously frozen sets. No predictions reconstructed here.
        for mode,r in (bundle.get('horizons') or {}).items():
            if mode not in MODES or r.get('status')!='ready' or r.get('recorded_at')!=record['finished_at']:
                continue
            try:
                validate_frozen(r)
                observed=time_ms(r['candle_closed_at']); seen=time_ms(record['finished_at'])
                if observed>seen or r.get('timeframe')!=MODES[mode][0] or r.get('reference')!='bitget/BTCUSDT/USDT-FUTURES': continue
                key=(mode,r['model_version'],observed)
                candidate=(r,path)
                if key not in samples: samples[key]=candidate
                elif samples[key][0] is not None and samples[key][0]['recorded_at']==r['recorded_at'] and samples[key][0]!=r:
                    samples[key]=(None,path)  # conflicting originals are not chosen by outcome
                item=dict(close=number(r['last_close']),score=r['momentum']['score'],volume=r['volume_ratio'])
                paths[mode].setdefault(observed,[]).append(item)
            except (KeyError,ValueError,TypeError):
                continue
    timeline={mode:sorted(points) for mode,points in paths.items()}
    results=[]
    for (mode,model,candle_at),(r,path) in sorted(samples.items()):
        if r is None:
            results.append(dict(mode=mode,model_version=model,status='conflicting_original',source_path=path));continue
        at=time_ms(r['recorded_at']);end=at+days*86400000;cutoff=min(end,now)
        period=PERIOD_MS[r['timeframe']];offset=4*86400000 if r['timeframe']=='1w' else 0
        first=((at-offset)//period+1)*period+offset
        expected=list(range(first,cutoff+1,period))
        actual=timeline[mode][bisect_right(timeline[mode],at):bisect_right(timeline[mode],cutoff)]
        valid=[];conflicts=0
        for t in actual:
            options=paths[mode][t]
            unique={json.dumps(x,sort_keys=True) for x in options}
            if len(unique)!=1: conflicts+=1;continue
            valid.append((t,options[0]))
        missing=len(set(expected)-{t for t,_ in valid})
        for s in r['scenarios']:
            activated=at if s['currently_supported'] else None
            targets=[];invalidated=None
            for t,data in valid:
                close=data['close'];direction=s['direction']
                if activated is None:
                    strong=s['id'].startswith('very_')
                    if ((close-s['trigger_price'])*direction>0 and data['score']*direction>0
                        and (not strong or data['volume'] is not None and data['volume']>=1.2)):
                        activated=t
                    # Do not award a target on the very candle used for activation.
                    continue
                if (close-s['invalidation_price'])*direction<0:
                    invalidated=t;break
                for i,target in enumerate(s['targets']):
                    forward_target=(not s['currently_supported'] or r['reference_price'] is None or (target['price']-r['reference_price'])*direction>0)
                    if forward_target and i not in [x['index'] for x in targets] and (close-target['price'])*direction>=0:
                        targets.append(dict(index=i,at=iso(t),price=target['price']))
            status=('incomplete_path' if missing or conflicts else 'pending' if now<end else
                    'not_activated' if activated is None else 'target_then_invalidated' if targets and invalidated else
                    'invalidated' if invalidated else 'target_reached' if targets else 'active_unresolved')
            results.append(dict(mode=mode,timeframe=r['timeframe'],model_version=model,
                scenario_set_id=r['scenario_set_id'],route=s['id'],recorded_at=r['recorded_at'],
                source_path=path,horizon_days=days,status=status,activated_at=iso(activated) if activated is not None else None,
                target_events=targets,invalidated_at=iso(invalidated) if invalidated else None,
                expected_closes=len(expected),observed_closes=len(valid),missing_closes=missing,conflicts=conflicts,
                preference_at_registration=r['preferred_scenario'],original_scenario=s,
                original_shb=(r.get('scenario_actions') or {}).get(s['id'])))
    return results


def build(root,output,as_of):
    records=read_records(root,as_of)
    results=[x for days in DAYS for x in evaluate(records,as_of,days)]
    level_history=[]
    for record,path in records:
        for mode,route in ((record.get('scenario_snapshot') or {}).get('horizons') or {}).items():
            try:
                validate_frozen(route)
                check=route['level_assessment']
                level_history.append(dict(mode=mode,recorded_at=route['recorded_at'],source_path=path,
                    scenario_set_id=route['scenario_set_id'],model_version=route['model_version'],
                    zone_timeframe=route['timeframe'],confirmation_timeframe=check['confirmation_timeframe'],
                    confirmation_closed_at=check['confirmation_closed_at'],reference_price=route['reference_price'],
                    selected=check['selected'],reaction=check['reaction'],vote=check['vote'],
                    scenario_actions=route.get('scenario_actions'),
                    current_disagrees=check['current_disagrees'],next_higher=check['next_higher'],next_lower=check['next_lower']))
            except (KeyError,TypeError,ValueError):
                continue
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    payload=dict(schema_version=2,evaluated_at=as_of,source_timeframes={'swing':'1d','position':'1w'},
        evaluation_horizons_days=list(DAYS),sample='first_published_per_mode_model_source_candle',
        scenario_results=results,level_check_history=level_history,
        note='Originele vier routes; geen achteraf voorspelde adviezen. Scenario-evaluatie gebruikt gesloten candles, geen intrabar fills.')
    (out/'btc-action-history.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    rows=[]
    for model in sorted({x['model_version'] for x in results if 'route' in x}):
        for mode in MODES:
            for days in DAYS:
                for route in ('very_bearish','bearish','bullish','very_bullish'):
                    subset=[x for x in results if x.get('mode')==mode and x.get('model_version')==model and x.get('horizon_days')==days and x.get('route')==route]
                    counts=[sum(x['status']==s for x in subset) for s in ('pending','incomplete_path','target_reached','invalidated','target_then_invalidated','not_activated','active_unresolved')]
                    if subset: rows.append('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [model,mode,days,route,len(subset),*counts])+'</tr>')
    (out/'btc-action-history.html').write_text('''<!doctype html><html lang="nl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BTC Niveau- en scenariocontrole</title><style>body{font:16px/1.6 system-ui;background:#0c1320;color:#edf3fc;max-width:1200px;margin:auto;padding:20px}a{color:#a9ccff}.table{overflow:auto}td,th{padding:9px;border-bottom:1px solid #30415b;text-align:left;white-space:nowrap}table{border-collapse:collapse}</style><a href="index.html">← Marktmeters</a><h1>Niveauchecks, scenario’s en kwaliteitscontrole</h1><p>Beoordeling na 7, 30 en 90 dagen. Bron-timeframe: dag voor swing, week voor positie. Eén eerste gepubliceerde set per modus, modelversie en afgesloten broncandle. Dat beperkt herhaling, maar de evaluatievensters kunnen nog overlappen; aantallen zijn niet automatisch onafhankelijk.</p><p>Alle vier oorspronkelijke routes worden beoordeeld, ook de routes die toen niet de voorkeur hadden. Activering, doelen en ongeldigverklaring worden op latere gesloten candles getoetst. De activeringscandle krijgt niet meteen een doeltreffer. Een gat in de vereiste opvolgcandles betekent onvolledig pad, geen succes. Wachtende horizonten zijn niet als compleet beoordeeld.</p><div class="table"><table><thead><tr>'''+''.join('<th>'+x+'</th>' for x in ('Model','Modus','Dagen','Route','Sets','Wachtend','Onvolledig','Doel','Ongeldig','Doel en later ongeldig','Niet geactiveerd','Onbeslist'))+'</tr></thead><tbody>'+(''.join(rows) or '<tr><td>Nog geen oorspronkelijke dag-/weekscenario’s opgeslagen. Geen historische adviezen gereconstrueerd.</td></tr>')+'''</tbody></table></div><h2>Geen tradeadvies of positietracking</h2><p>Deze evaluatie beoordeelt marktanalyses en mogelijke vervolgzones, niet jouw transacties of rendement. SHB beschrijft voorwaarden per oorspronkelijk scenario; er worden geen posities, echte orders of rendementen gevolgd. HOLD bevestigt geen persoonlijke stop.</p><h2>Kwaliteit vóór verbetering</h2><p>Voorspellende waarde is nog niet bewezen. Geen scorepercentage uit kleine of afhankelijke steekproeven. Eerst datadekking, regelchecks, oorspronkelijke scenario’s en versiebeheer controleren. Daarna vooraf vastgelegde aanpassingen op toekomstige ongebruikte data toetsen. Maand-, kwartaal- en jaarcontrole passen niet automatisch gewichten aan.</p><p><a href="btc-action-history.json">Oorspronkelijke scenario’s, uitkomsten en evaluatiegegevens (JSON)</a></p></html>''',encoding='utf-8')


if __name__=='__main__':
    import sys
    build(sys.argv[1],sys.argv[2],datetime.now(timezone.utc).isoformat())
