"""Per-run report readiness and recurring blockers; no invented market verdicts."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

WINDOW = 14400000
METHOD = 'bitget_history_exhaustion_and_exact_volume_v1'


def mapping(value):
    return value if isinstance(value,dict) else {}


def stamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone required')
    return int(dt.timestamp()*1000)


def finite(value, positive=False):
    try:
        number = Decimal(str(value))
        return number.is_finite() and (not positive or number>0)
    except (InvalidOperation, ValueError, TypeError):
        return False


def assess(record, as_of):
    """Scope-specific readiness. Snapshot status ok alone is never report success."""
    now = stamp(as_of)
    record = record if isinstance(record,dict) else {}
    issues = []
    try:
        measured = stamp(record['finished_at'])
        source_ok = ((record.get('exchange'),record.get('market'),record.get('symbol')) ==
                     ('bitget','USDT-FUTURES','BTCUSDT') and 0<=now-measured<=18000000)
    except (KeyError, ValueError, TypeError, AttributeError):
        measured, source_ok = None, False
    if not source_ok:
        issues.append(dict(code='source_identity_or_freshness', action='Controleer bronidentiteit en meettijden.'))
    metrics = mapping(record.get('metrics'))
    price = mapping(metrics.get('futures_price'))
    data = mapping(price.get('data'))
    price_ok = source_ok and price.get('status')=='ok' and finite(data.get('lastPr'),True)
    try:
        price_ok = price_ok and 0<=now-stamp(price['observed_at'])<=18000000 and data['symbol']=='BTCUSDT'
    except (KeyError,ValueError,TypeError):
        price_ok = False
    candle = mapping(metrics.get('candles_4h'))
    cd = mapping(candle.get('data'))
    rows = cd.get('candles') or []
    candles_ok = source_ok and candle.get('status')=='ok' and cd.get('closed_only') is True and bool(rows)
    try:
        times = [r['open_time_ms'] for r in rows]
        end = measured//WINDOW*WINDOW
        candles_ok = (candles_ok and cd.get('interval')=='4H' and cd.get('gap_count')==0 and
                      all(type(t) is int and t%WINDOW==0 and t+WINDOW<=now for t in times) and
                      all(b-a==WINDOW for a,b in zip(times,times[1:])) and times[-1]+WINDOW==end and
                      all(all(finite(r[k],True) for k in ('open','high','low','close')) and
                          float(r['low'])<=min(float(r['open']),float(r['close']))<=
                          max(float(r['open']),float(r['close']))<=float(r['high']) and
                          all(finite(r[k]) and Decimal(str(r[k]))>=0 for k in
                              ('base_volume_btc','quote_volume_usdt')) for r in rows))
    except (KeyError,ValueError,TypeError,IndexError):
        candles_ok = False
    if not price_ok:
        issues.append(dict(code='price_unavailable',action='Herstel actuele prijsbron; geen richting uit een oude prijs.'))
    if not candles_ok:
        issues.append(dict(code='closed_4h_candles_unavailable',action='Herstel aaneengesloten afgesloten 4H-candles.'))
    for name, metric in metrics.items():
        if not isinstance(metric,dict) or metric.get('status')!='ok':
            issues.append(dict(code='metric_'+name,action='Herstel bron of verwerking van dit meetonderdeel.'))
    native=mapping(mapping(metrics.get('multi_timeframe')).get('data'))
    if __package__:
        from .multi_timeframe_signals import assess as assess_signal
    else:
        from multi_timeframe_signals import assess as assess_signal
    for tf, metric in native.items():
        try:
            if metric.get('status')!='ok':
                raise ValueError('timeframe unavailable')
            expected=assess_signal(metric['data']['candles'],tf,metric['observed_at'])
            if expected.get('status')!='provisional' or metric.get('signal')!=expected:
                raise ValueError('timeframe processing mismatch')
        except (KeyError,ValueError,TypeError,AttributeError):
            issues.append(dict(code='timeframe_'+tf,
                               action='Herbereken timeframe uit de eigen afgesloten broncandles.'))
    cvd = mapping(record.get('cvd_4h'))
    markets = mapping(cvd.get('markets'))
    verified = []
    for market in ('spot','usdt_futures'):
        m = mapping(markets.get(market))
        try:
            valid = (source_ok and m.get('status')=='ok' and m.get('coverage_verified') is True and
                     m.get('coverage_method')==METHOD and m.get('coverage_scope')=='bitget_public_history_only' and
                     (m.get('exchange'),m.get('symbol'),m.get('market'),m.get('unit'))==
                     ('bitget','BTCUSDT',market,'BTC') and finite(m.get('validated_delta_btc')) and
                     m.get('interval_end_ms')==measured//WINDOW*WINDOW and
                     m.get('interval_start_ms')==measured//WINDOW*WINDOW-WINDOW)
        except (TypeError,ValueError):
            valid = False
        if valid:
            verified.append(market)
        else:
            reason = mapping(m.get('recovery')).get('reason','no_verified_history')
            issues.append(dict(code='cvd_'+market, detail=reason,
                action='Controleer historische pagina’s en volumeverschil; herprobeer via bestaande NAS-upload.'))
    scenario_ok = True
    if 'scenario_snapshot' in record:
        try:
            if __package__:
                from .scenario_archive import freeze
            else:
                from scenario_archive import freeze
            scenario_ok = record['scenario_snapshot'] == freeze(record)
        except (KeyError,ValueError,TypeError,AttributeError,OverflowError):
            scenario_ok = False
        if not scenario_ok:
            issues.append(dict(code='scenario_input_output_mismatch',
                               action='Herbereken scenario’s uit de oorspronkelijke invoer; onderzoek verschil.'))
    return dict(schema_version=1, checked_at=as_of, measurement_at=record.get('finished_at'),
                valid_until=datetime.fromtimestamp(min(measured+18000000,(measured//WINDOW+1)*WINDOW)/1000,timezone.utc).isoformat() if measured is not None else None,
                scenario_processing='consistent' if scenario_ok else 'rejected',
                status='ready_for_scoped_report' if price_ok and candles_ok and len(verified)==2 and scenario_ok and not issues else 'degraded',
                price_structure='available' if price_ok and candles_ok else 'unavailable',
                bitget_interval_delta='available' if len(verified)==2 else 'unavailable',
                verified_delta_markets=verified, macro_cycle_verdict='requires_separate_macro_evidence',
                issues=issues,
                interpretation='Gebruik geldige onderdelen met hun eigen scope; ontbrekend is geen neutraal oordeel.')


def report_text_findings(text):
    """Conservative explicit contradiction check, not a fact-checking oracle."""
    if re.search(r'macro[^\n]{0,90}neutraal[^\n]{0,90}(?:onvoldoende data|ontbre)',text,re.I):
        return ['missing_macro_presented_as_neutral']
    return []


def report_findings(root):
    """Audit latest original report per kind without rewriting report history."""
    result = []
    try:
        entries = json.loads((Path(root)/'reports/index.json').read_text()).get('reports',[])
    except (OSError,ValueError,AttributeError):
        return [dict(code='report_archive_unavailable')]
    seen = set()
    for entry in sorted(entries,key=lambda e:e.get('reported_at',''),reverse=True):
        kind = entry.get('monitor')
        if kind in seen:
            continue
        seen.add(kind)
        try:
            p=Path(entry['path'])
            if p.is_absolute() or '..' in p.parts or p.parts[:1]!=('reports',):
                raise ValueError('invalid path')
            raw=json.loads((Path(root)/p).read_text())
            if __package__:
                from .monitor_archive import validate_record
            else:
                from monitor_archive import validate_record
            validate_record(raw)
            text=raw['report_text']
            # Inadequate evidence must not be restated as a neutral macro verdict.
            if report_text_findings(text):
                result.append(dict(code='missing_macro_presented_as_neutral', monitor=kind,
                                   path=p.as_posix(), action='Schrijf macro: niet vast te stellen; behoud origineel.'))
        except (OSError,ValueError,KeyError,TypeError):
            result.append(dict(code='invalid_original_report',monitor=kind))
    return result


def review(feed, as_of, root='.'):
    """Repeated snapshots of one 4H interval are not independent failures."""
    records=feed.get('measurements') or []
    current=assess(records[0] if records else {},as_of)
    # Count only actual NAS observations, newest record per closed interval. No
    # cloud run without a journal can supersede a NAS recovery for that interval.
    intervals={}
    for record in records:
        if record.get('collection_source')!='nas':
            continue
        try:
            end=stamp(record['finished_at'])//WINDOW*WINDOW
            quality=assess(record,record['finished_at'])
            intervals.setdefault(end,quality)
        except (ValueError,KeyError,TypeError):
            continue
    recurring=[]
    for code in ('cvd_spot','cvd_usdt_futures'):
        affected=[end for end,q in intervals.items() if any(i['code']==code for i in q['issues'])]
        if len(affected)>=2:
            recurring.append(dict(code=code,affected_closed_intervals=len(affected),
                                  action='Terugkerende blokkade: onderzoek en volg herstel; niet alleen ONTBREEKT herhalen.'))
    return dict(current=current,recurring_blockers=recurring,
                report_findings=report_findings(root),
                scope='Engineering en rapportconsistentie; geen bewijs van voorspellende kwaliteit.')


def render(feed, as_of):
    from html import escape
    records=feed.get('measurements') or []
    q=assess(records[0] if records else {},as_of)
    label='Gecontroleerd voor beperkte bronscope' if q['status']=='ready_for_scoped_report' else 'BEPERKT — onderdelen afgekeurd'
    lines=''.join('<li>'+escape(i['code'])+': '+escape(i['action'])+'</li>' for i in q['issues'])
    return ('<section class="panel" id="analysis-quality" data-valid-until="'+escape(q['valid_until'] or '')+'" style="margin-bottom:24px">'
            '<h2>Datakwaliteit en rapportbruikbaarheid</h2><p>'+label+'</p>'
            '<p id="quality-scope">Prijsstructuur: '+escape(q['price_structure'])+' · Bitget-intervaldelta: '+
            escape(q['bitget_interval_delta'])+'. Macro-oordeel vereist afzonderlijk bewijs.</p>'
            '<p>Controle op '+escape(as_of)+'. Een geslaagde upload is geen volledige analyse.</p>'
            '<ul>'+lines+'</ul><p><a href="btc-status.html">Actuele kwaliteits- en taakstatus →</a></p></section>')


def stage(feed_path, destination, as_of=None):
    """Recheck source and generated assets before upload; degraded data stay visible.

    Broken assets fail the build. Source limitations publish an explicit degraded
    result so an old green dashboard is not left live by a failed data gate.
    """
    as_of=as_of or datetime.now(timezone.utc).isoformat()
    feed=json.loads(Path(feed_path).read_text())
    folder=Path(destination)
    result=review(feed,as_of,Path(feed_path).resolve().parent.parent)
    required=('index.html','btc-dashboard.html','btc-status.html','btc-timeframes.html',
              'btc-signal-history.html','status.mjs','status.css')
    absent=[name for name in required if not (folder/name).is_file()]
    if absent:
        raise ValueError('Dashboard assets missing: '+', '.join(absent))
    if 'id="analysis-quality"' not in (folder/'index.html').read_text():
        raise ValueError('Dashboard quality panel missing')
    from scripts.elliott_dashboard import build as build_elliott
    from scripts.elliott_history import read as read_elliott_history
    visual = build_elliott(feed, as_of, read_elliott_history(Path(feed_path).resolve().parent.parent,as_of))
    page = (folder/'index.html').read_text()
    if 'id="elliott-scenarios"' not in page:
        raise ValueError('Elliott visual panel missing')
    charts = 2*sum(h['status']=='available' for h in visual['horizons'])
    if page.count('class="ew-chart"') != charts:
        raise ValueError('Elliott source/chart count mismatch')
    result['elliott_visuals'] = dict(source_status=visual['status'], charts=charts,
                                    current_wave='unproven', nested_count='unproven',
                                    coverage={h['timeframe']:h.get('coverage',{}) for h in visual['horizons']})
    result['dashboard_assets']='checked'
    (folder/'btc-quality.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    return result


if __name__=='__main__':
    import sys
    stage(sys.argv[1],sys.argv[2])
