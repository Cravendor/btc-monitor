"""One bounded, immutable recheck of the 27 October 12–16 UTC source conflict."""
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode
from scripts import elliott_history as history
from scripts import source_revision_audit as audit
from scripts.enrich import BASE, request
from scripts.market_scenarios import iso,time_ms

MODEL='bitget_conflict_window_probe_v1'
START=1793102400000
END=1793116800000
DIR='data/history/source-window-audits'
OUTPUT='output/source-window-audit.json'
FIELDS=('open','high','low','close','base_volume_btc','quote_volume_usdt')


def decimal_fields(raw):
    return {field:Decimal(str(value)) for field,value in zip(FIELDS,raw[1:7])}


def build(root='.',as_of=None,requester=request):
    as_of=as_of or datetime.now(timezone.utc).isoformat()
    now=time_ms(as_of)
    result=dict(model_version=MODEL,exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',
                as_of=as_of,start=iso(START),end=iso(END),activation='none',
                status='incomplete',sources=[],cache=[],comparison=None)
    if now<END:
        result['reason']='window_not_yet_closed';return result
    current={}
    for tf in ('4h','1h'):
        period=history.PERIOD_MS[tf]
        entry=dict(timeframe=tf,status='unavailable');result['sources'].append(entry)
        path=history.filename(Path(root)/history.DIRECTORY,tf)
        cache=dict(timeframe=tf,status='unavailable');result['cache'].append(cache)
        try:
            raw=path.read_bytes();rows,_=history.load(path,tf,history.floor_time(now,tf))
            if path.read_bytes()!=raw:raise ValueError('cache_changed')
            selected=[rows[t] for t in range(START,END,period)]
            cache.update(status='available',file_sha256=hashlib.sha256(raw).hexdigest(),rows=selected)
        except (OSError,ValueError,KeyError,TypeError):
            cache['reason']='cache_missing_or_invalid'
        url=BASE+'mix/market/history-candles?'+urlencode(dict(symbol='BTCUSDT',
            productType='USDT-FUTURES',granularity=history.GRANULARITIES[tf],
            startTime=START-period,endTime=END,limit=10))
        entry['url']=url
        try:
            reply=requester(url,lambda p:audit.source_rows(p,tf,START,END),True)
            observed=reply['observed_at'];t=time_ms(observed)
            if not now-60000<=t<=now+120000 or reply.get('status')!='ok':
                raise ValueError('source_invalid')
            payload=reply['data'];again=audit.source_rows(payload['source_rows'],tf,START,END)
            if again['rows']!=payload['rows']:raise ValueError('normalization_mismatch')
            selected={int(x[0]):x for x in again['source_rows'] if START<=int(x[0])<END}
            if set(selected)!=set(range(START,END,period)):
                raise ValueError('incomplete_window')
            current[tf]=selected
            entry.update(status='available',observed_at=observed,source_rows=again['source_rows'],
                         source_rows_sha256=audit.digest(again['source_rows']))
        except (OSError,ValueError,KeyError,TypeError,OverflowError):
            entry['reason']='source_unavailable_or_invalid'
    if len(current)!=2 or any(c['status']!='available' for c in result['cache']):
        result['reason']='source_or_cache_unavailable';return result
    parent=decimal_fields(current['4h'][START])
    parts=[decimal_fields(current['1h'][t]) for t in range(START,END,history.PERIOD_MS['1h'])]
    aggregate=dict(open=parts[0]['open'],high=max(p['high'] for p in parts),
                   low=min(p['low'] for p in parts),close=parts[-1]['close'],
                   base_volume_btc=sum((p['base_volume_btc'] for p in parts),Decimal(0)),
                   quote_volume_usdt=sum((p['quote_volume_usdt'] for p in parts),Decimal(0)))
    differences={k:dict(native=str(parent[k]),aggregate=str(aggregate[k]),
                         native_minus_aggregate=str(parent[k]-aggregate[k]))
                 for k in FIELDS if parent[k]!=aggregate[k]}
    cache_changes=[]
    for cache in result['cache']:
        for old in cache['rows']:
            new=decimal_fields(current[cache['timeframe']][old['open_time_ms']])
            fields={k:dict(cached=str(old[k]),fresh=str(new[k])) for k in FIELDS
                    if Decimal(str(old[k]))!=new[k]}
            if fields:cache_changes.append(dict(timeframe=cache['timeframe'],opened_at=iso(old['open_time_ms']),fields=fields))
    result.update(status='checked',comparison=dict(differences=differences,
                  price_and_base_match=not any(k in differences for k in FIELDS[:-1]),
                  quote_volume='diagnostic_only',cache_changes=cache_changes))
    return result


def existing_completed(root):
    directory=Path(root)/DIR
    for p in sorted(directory.glob('*.json')):
        try:
            d=json.loads(p.read_text(encoding='utf-8'))
            if p.name != datetime.fromtimestamp(time_ms(d['as_of'])/1000,timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+audit.digest(d)+'.json':
                raise ValueError('existing_probe_hash_mismatch')
            if d.get('model_version')==MODEL and d.get('start')==iso(START) and d.get('end')==iso(END) and d.get('status')=='checked':
                return p
        except (OSError,ValueError,KeyError,TypeError) as exc:
            raise ValueError('existing_probe_invalid') from exc
    return None


def save(root,record):
    directory=Path(root)/DIR;directory.mkdir(parents=True,exist_ok=True)
    stamp=datetime.fromtimestamp(time_ms(record['as_of'])/1000,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path=directory/(stamp+'-'+audit.digest(record)+'.json');body=audit.canonical(record)+'\n';tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=directory.parent,delete=False) as f:
            tmp=Path(f.name);f.write(body)
        try:os.link(tmp,path)
        except FileExistsError:
            if path.read_text(encoding='utf-8')!=body:raise ValueError('probe_collision')
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)
    return path


def run(root='.',requester=request):
    prior=existing_completed(root)
    if prior:return dict(status='already_checked',path=prior.relative_to(root).as_posix())
    record=build(root,requester=requester);path=save(root,record)
    artifact=Path(root)/OUTPUT;artifact.parent.mkdir(parents=True,exist_ok=True)
    artifact.write_text(audit.canonical(record)+'\n',encoding='utf-8')
    return dict(status=record['status'],path=path.relative_to(root).as_posix())


if __name__=='__main__':
    try:print(json.dumps(run()))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'error','reason':str(exc)}));raise SystemExit(1)
