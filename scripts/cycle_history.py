"""Resumable public Bitget BTCUSDT futures daily history, separate from NAS runs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
try:
    from .enrich import request, BASE
    from .market_scenarios import time_ms, iso, number
except ImportError:
    from enrich import request, BASE
    from market_scenarios import time_ms, iso, number

DAY=86400000
START='2021-01-01T00:00:00Z'
PATH='data/history/bitget_btcusdt_daily.json'
MODEL='bitget_daily_history_v1'
FIELDS=('open','high','low','close','base_volume_btc','quote_volume_usdt')


def checked(c, boundary):
    t=c.get('open_time_ms')
    if type(t) is not int or t<0 or t%DAY or t>=boundary:raise ValueError('invalid or open daily candle')
    v=[number(c.get(k)) for k in FIELDS]
    o,h,l,close,base,quote=v
    if min(o,h,l,close)<=0 or min(base,quote)<0 or l>min(o,close) or h<max(o,close):
        raise ValueError('invalid daily OHLC/volume')
    return dict(open_time_ms=t,**dict(zip(FIELDS,v)))


def rows_from(payload, boundary):
    if not isinstance(payload,list) or len(payload)>200:raise ValueError('invalid historical response')
    output={}
    for raw in payload:
        if not isinstance(raw,(list,tuple)) or len(raw)<7:raise ValueError('invalid candle row')
        t=raw[0]
        if isinstance(t,bool) or not str(t).isdigit():raise ValueError('invalid daily timestamp')
        if int(t)==boundary:continue  # Exclude a returned in-progress day at the upper edge.
        c=checked(dict(open_time_ms=int(t),**dict(zip(FIELDS,raw[1:7]))),boundary)
        if c['open_time_ms'] in output and output[c['open_time_ms']]!=c:raise ValueError('conflicting duplicate day')
        output[c['open_time_ms']]=c
    return output


def load(path, boundary):
    if not Path(path).exists():return {},[]
    data=json.loads(Path(path).read_text())
    if (data.get('schema_version'),data.get('model_version'),data.get('exchange'),data.get('market'),data.get('symbol'),data.get('interval')) != (1,MODEL,'bitget','USDT-FUTURES','BTCUSDT','1d'):
        raise ValueError('wrong historical source identity')
    rows={}
    for item in data['candles']:
        c=checked(item,boundary)
        if c['open_time_ms'] in rows:raise ValueError('duplicate cached day')
        rows[c['open_time_ms']]=c
    digest=hashlib.sha256(json.dumps([rows[t] for t in sorted(rows)],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=data.get('content_sha256'):raise ValueError('history checksum mismatch')
    return rows,data.get('pages',[])


def report(rows, pages, start, boundary, as_of, reason):
    missing=[t for t in range(start,boundary,DAY) if t not in rows]
    candles=[rows[t] for t in sorted(rows)]
    return dict(schema_version=1,model_version=MODEL,exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',
        interval='1d',closed_only=True,status='complete' if not missing else 'partial',
        requested_from=iso(start),required_through=iso(boundary),checked_at=as_of,
        candle_count=len(candles),required_days=(boundary-start)//DAY,missing_days=len(missing),
        first_missing_at=iso(missing[0]) if missing else None,
        first_candle_at=iso(min(rows)) if rows else None,
        last_candle_at=iso(max(rows)) if rows else None,reason=reason,pages=pages,candles=candles,
        content_sha256=hashlib.sha256(json.dumps(candles,sort_keys=True,separators=(',',':')).encode()).hexdigest())


def save(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
    temporary.replace(path)


def run(path=PATH, as_of=None, start=START, max_pages=32, seconds=150, requester=request, clock=time.monotonic):
    as_of=as_of or datetime.now(timezone.utc).isoformat()
    now=time_ms(as_of);boundary=now//DAY*DAY;left=time_ms(start)
    if left<0 or left%DAY or left>=boundary or (boundary-left)//DAY>6000:raise ValueError('invalid history range')
    if type(max_pages) is not int or not 1<=max_pages<=40 or not 1<=seconds<=300:raise ValueError('invalid budget')
    rows,pages=load(path,boundary);deadline=clock()+seconds;reason='page_budget'
    for unused in range(max_pages):
        missing=next((t for t in range(left,boundary,DAY) if t not in rows),None)
        if missing is None:reason='complete';break
        if clock()+15>deadline:reason='time_budget';break
        end=min(missing+84*DAY,boundary)
        # One preceding day avoids losing an exclusive lower-bound candle.
        url=BASE+'mix/market/history-candles?'+urlencode(dict(symbol='BTCUSDT',productType='USDT-FUTURES',
            granularity='1Dutc',startTime=missing-DAY,endTime=end,limit=200))
        result=requester(url,lambda data:rows_from(data,boundary),True)
        if result.get('status')!='ok':reason='source_unavailable';break
        received=result['data']
        if any(t<missing-DAY or t>end for t in received):reason='unexpected_response_window';break
        expected=range(missing,end,DAY)
        if any(t not in received for t in expected):reason='incomplete_response_window';break
        if any(t in rows and rows[t]!=c for t,c in received.items()):reason='source_revision_conflict';break
        for t in expected:rows.setdefault(t,received[t])
        pages.append(dict(start=iso(missing),end=iso(end),url=url,observed_at=result.get('observed_at',as_of),days=(end-missing)//DAY))
        save(path,report(rows,pages,left,boundary,as_of,'checkpoint'))
    data=report(rows,pages,left,boundary,as_of,reason)
    if data['status']=='complete':data['reason']='complete'
    save(path,data)
    return data


def reference(path, as_of):
    """Local read only: independently check coverage, never trust cached status."""
    missing=dict(status='unavailable',reason='Meerjarige daghistorie nog niet beschikbaar.')
    try:
        boundary=time_ms(as_of)//DAY*DAY;rows,pages=load(path,boundary)
        if not rows:return missing
        # The fixed collection target is not a selected cycle boundary.
        data=report(rows,pages,time_ms(START),boundary,as_of,'read_only_validation')
        return {k:v for k,v in data.items() if k not in ('candles','pages')}
    except (ValueError,KeyError,TypeError,OSError,OverflowError):return missing


def render_reference(feed):
    from html import escape
    m=(feed.get('measurements') or [{}])[0]
    r=m.get('cycle_history_reference') or {}
    if not r:return ''
    esc=lambda x:escape(str(x),quote=True)
    return ('<details><summary>Meerjarige koershistorie</summary><p>Bitget BTCUSDT USDT-FUTURES · dagcandles. Status: '+esc(r.get('status','unavailable'))+
        '. Gecontroleerde dagen: '+esc(r.get('candle_count',0))+'. Ontbrekend: '+esc(r.get('missing_days','onbekend'))+
        '.</p><p>Gewenste dekking vanaf '+esc(r.get('requested_from',START))+' tot '+esc(r.get('required_through','onbekend'))+
        '. Dit is datadekking, geen vastgestelde cyclusindeling. Bronbeoordeling bij meting: '+esc(m.get('finished_at','onbekend'))+'.</p></details>')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--path',default=PATH);p.add_argument('--start',default=START)
    p.add_argument('--max-pages',type=int,default=32);p.add_argument('--seconds',type=int,default=150)
    a=p.parse_args();r=run(a.path,start=a.start,max_pages=a.max_pages,seconds=a.seconds)
    print(json.dumps({k:v for k,v in r.items() if k not in ('candles','pages')},indent=2))
    return 0 if r['status']=='complete' else 1

if __name__=='__main__':raise SystemExit(main())
