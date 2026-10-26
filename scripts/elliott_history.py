"""Bounded, resumable native candle history for Elliott inspection, July 2025+."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from scripts.enrich import BASE, request
from scripts.market_scenarios import time_ms, iso, number
from scripts.native_timeframe_candles import PERIOD_MS, GRANULARITIES
from scripts.cycle_history import FIELDS, load as load_daily, save

START = '2025-07-01T00:00:00Z'
MODEL = 'bitget_elliott_history_v1'
TF = ('1w', '4h', '1h')
DIRECTORY = 'data/history/elliott'


def floor_time(t, tf):
    offset = 4*86400000 if tf == '1w' else 0
    return (t-offset)//PERIOD_MS[tf]*PERIOD_MS[tf]+offset


def checked(c, tf, boundary):
    t = c.get('open_time_ms')
    if type(t) is not int or t < 0 or floor_time(t,tf) != t or t >= boundary:
        raise ValueError('invalid or open candle')
    values = [number(c.get(k)) for k in FIELDS]
    o,h,l,close,base,quote = values
    if min(o,h,l,close) <= 0 or min(base,quote) < 0 or l > min(o,close) or h < max(o,close):
        raise ValueError('invalid OHLC/volume')
    return dict(open_time_ms=t, **dict(zip(FIELDS,values)))


def rows_from(payload, tf, boundary):
    if not isinstance(payload,list) or len(payload)>200:
        raise ValueError('invalid historical response')
    rows = {}
    for raw in payload:
        if not isinstance(raw,(list,tuple)) or len(raw)<7 or isinstance(raw[0],bool) or not str(raw[0]).isdigit():
            raise ValueError('invalid candle row')
        if int(raw[0]) == boundary:
            continue
        c = checked(dict(open_time_ms=int(raw[0]),**dict(zip(FIELDS,raw[1:7]))),tf,boundary)
        if c['open_time_ms'] in rows and rows[c['open_time_ms']] != c:
            raise ValueError('conflicting duplicate')
        rows[c['open_time_ms']] = c
    return rows


def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def filename(directory, tf):
    return Path(directory)/('bitget_btcusdt_'+tf+'.json')


def load(path, tf, boundary):
    if not Path(path).exists():
        return {},[]
    data = json.loads(Path(path).read_text())
    if (data.get('schema_version'),data.get('model_version'),data.get('exchange'),data.get('market'),
        data.get('symbol'),data.get('interval'),data.get('closed_only')) != (
            1,MODEL,'bitget','USDT-FUTURES','BTCUSDT',tf,True):
        raise ValueError('wrong history identity')
    rows = {}
    for c in data['candles']:
        c = checked(c,tf,boundary)
        if c['open_time_ms'] in rows:
            raise ValueError('duplicate cached candle')
        rows[c['open_time_ms']] = c
    if digest([rows[t] for t in sorted(rows)]) != data.get('content_sha256'):
        raise ValueError('history checksum mismatch')
    return rows,data['pages']


def coverage(rows, tf, as_of):
    start = floor_time(time_ms(START),tf)
    boundary = floor_time(time_ms(as_of),tf)
    expected = range(start,boundary,PERIOD_MS[tf])
    missing = [t for t in expected if t not in rows]
    return dict(status='complete' if not missing else 'partial',requested_from=START,
                effective_from=iso(start),required_through=iso(boundary),
                required_candles=len(expected),candle_count=sum(t in rows for t in expected),
                missing_candles=len(missing),first_missing_at=iso(missing[0]) if missing else None)


def report(rows, pages, tf, as_of, reason):
    candles = [rows[t] for t in sorted(rows)]
    return dict(schema_version=1,model_version=MODEL,exchange='bitget',market='USDT-FUTURES',
                symbol='BTCUSDT',interval=tf,closed_only=True,checked_at=as_of,
                **coverage(rows,tf,as_of),reason=reason,pages=pages,candles=candles,
                content_sha256=digest(candles))


def run(directory=DIRECTORY, as_of=None, max_pages=12, seconds=90, requester=request, clock=time.monotonic):
    """Round-robin pages; atomic checkpoint after each complete response.

    No early gap is bridged, conflicting originals are never overwritten, and
    a failed degree does not prevent independent degrees from being checkpointed.
    """
    as_of = as_of or datetime.now(timezone.utc).isoformat()
    if type(max_pages) is not int or not 1<=max_pages<=40 or not 16<=seconds<=180:
        raise ValueError('invalid batch budget')
    now = time_ms(as_of)
    if now <= time_ms(START) or now-time_ms(START) > 8*366*86400000:
        raise ValueError('unsupported history range')
    states = {}
    for tf in TF:
        boundary = floor_time(now,tf)
        rows,pages = load(filename(directory,tf),tf,boundary)
        states[tf] = dict(rows=rows,pages=pages,reason='page_budget')
    deadline=clock()+seconds
    attempts=0
    blocked=set()
    while attempts<max_pages:
        progress=False
        for tf in TF:
            if tf in blocked or attempts>=max_pages:
                continue
            s=states[tf]; q=coverage(s['rows'],tf,as_of)
            if q['status']=='complete':
                s['reason']='complete';continue
            if clock()+15>deadline:
                s['reason']='time_budget';blocked.add(tf);continue
            period=PERIOD_MS[tf];boundary=floor_time(now,tf)
            missing=time_ms(q['first_missing_at'])
            # Weekly windows stay below 90 days; intraday pages below 200 rows,
            # including a possible preceding/upper-bound candle from the API.
            size=11 if tf=='1w' else 192
            end=min(missing+size*period,boundary)
            url=BASE+'mix/market/history-candles?'+urlencode(dict(symbol='BTCUSDT',
                productType='USDT-FUTURES',granularity=GRANULARITIES[tf],
                startTime=missing-period,endTime=end,limit=200))
            result=requester(url,lambda data,tf=tf,b=boundary:rows_from(data,tf,b),True)
            attempts+=1
            reason=None
            received=result.get('data')
            if result.get('status')!='ok' or not isinstance(received,dict):
                reason='source_unavailable'
            elif any(t<missing-period or t>end for t in received):
                reason='unexpected_response_window'
            elif any(t not in received for t in range(missing,end,period)):
                reason='incomplete_response_window'
            elif any(t in s['rows'] and s['rows'][t]!=c for t,c in received.items()):
                reason='source_revision_conflict'
            if reason:
                s['reason']=reason;blocked.add(tf);continue
            for t in range(missing,end,period):
                s['rows'].setdefault(t,received[t])
            s['pages'].append(dict(start=iso(missing),end=iso(end),url=url,
                                   observed_at=result.get('observed_at',as_of),candles=(end-missing)//period))
            save(filename(directory,tf),report(s['rows'],s['pages'],tf,as_of,'checkpoint'))
            progress=True
        if not progress:
            break
    output={}
    for tf,s in states.items():
        q=report(s['rows'],s['pages'],tf,as_of,s['reason'])
        if q['status']=='complete':q['reason']='complete'
        save(filename(directory,tf),q)
        output[tf]={k:v for k,v in q.items() if k not in ('candles','pages')}
    return output


def read(root, as_of):
    """Read-only chart inputs; independently recheck requested coverage per degree."""
    root=Path(root);out={};daily_rows={}
    for tf in ('1w','1d','4h','1h'):
        try:
            if tf=='1d':
                path=root/'data/history/bitget_btcusdt_daily.json'
                rows,pages=load_daily(path,floor_time(time_ms(as_of),tf))
                daily_rows=rows
            else:
                path=filename(root/DIRECTORY,tf)
                rows,pages=load(path,tf,floor_time(time_ms(as_of),tf))
            q=coverage(rows,tf,as_of)
            start=floor_time(time_ms(START),tf)
            boundary=floor_time(time_ms(as_of),tf)
            q.update(rows=[rows[t] for t in sorted(rows) if start<=t<boundary],
                     source_path=path.relative_to(root).as_posix(),timeframe=tf,
                     source_at=max((p.get('observed_at','') for p in pages),default=''))
            out[tf]=q
        except (OSError,ValueError,KeyError,TypeError,OverflowError):
            out[tf]=dict(status='unavailable',rows=[],timeframe=tf,reason='history_unavailable_or_invalid')
    for child,parent in (('1h','4h'),('4h','1d'),('1d','1w')):
        source=daily_rows if child=='1d' else {r['open_time_ms']:r for r in out[child]['rows']}
        check=reconcile(source,out[parent]['rows'],child,parent)
        out[parent]['cross_timeframe_check']=check
        if check['mismatch_candles']:
            out[parent]['status']='conflict'
            out[parent]['reason']='cross_timeframe_price_or_base_volume_conflict'
    return out


def reconcile(source, parents, child, parent):
    """Compare only complete groups; quote-volume differences remain diagnostics.

    These normalized values cannot establish raw feed rounding precision. This
    candle-price check does not change the separate exact CVD coverage rule.
    """
    checked_count=0;skipped=0;bad=[];details=[];quote_delta=Decimal(0)
    for row in parents:
        start=row['open_time_ms']
        piece=[source.get(t) for t in range(start,start+PERIOD_MS[parent],PERIOD_MS[child])]
        if any(c is None for c in piece):
            skipped+=1;continue
        checked_count+=1
        calculated=dict(open=piece[0]['open'],high=max(c['high'] for c in piece),
                        low=min(c['low'] for c in piece),close=piece[-1]['close'])
        base=sum(Decimal(str(c['base_volume_btc'])) for c in piece)
        calculated['base_volume_btc']=base
        differences={}
        for field,value in calculated.items():
            native=Decimal(str(row[field]));aggregated=Decimal(str(value))
            if native!=aggregated:
                differences[field]=dict(native=str(native),from_children=str(aggregated),
                                        native_minus_children=str(native-aggregated))
        if differences:
            bad.append(iso(start))
            if len(details)<5:
                details.append(dict(opened_at=iso(start),fields=differences))
        quote=sum(Decimal(str(c['quote_volume_usdt'])) for c in piece)
        quote_delta=max(quote_delta,abs(quote-Decimal(str(row['quote_volume_usdt']))))
    return dict(child=child,parent=parent,checked_candles=checked_count,
                skipped_incomplete_groups=skipped,mismatch_candles=len(bad),
                first_mismatch_at=bad[0] if bad else None,
                mismatch_details=details,mismatch_details_truncated=len(bad)>len(details),
                status='conflict' if bad else 'consistent_checked_groups' if checked_count else 'not_checked',
                quote_volume_max_abs_difference_usdt=str(quote_delta),quote_volume_scope='diagnostic_only_normalized_values')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',default=DIRECTORY)
    p.add_argument('--max-pages',type=int,default=12)
    p.add_argument('--seconds',type=int,default=90)
    a=p.parse_args();result=run(a.directory,max_pages=a.max_pages,seconds=a.seconds)
    print(json.dumps(result,indent=2))
    if a.directory==DIRECTORY:
        as_of=datetime.now(timezone.utc).isoformat()
        reviewed=read('.',as_of)
        summary=dict(schema_version=1,checked_at=as_of,requested_from=START,
                     exchange='bitget',market='USDT-FUTURES',symbol='BTCUSDT',
                     timeframes={tf:{k:v for k,v in q.items() if k!='rows'} for tf,q in reviewed.items()})
        save(Path(DIRECTORY)/'coverage.json',summary)
        # Coverage can be complete while reconciliation fails. Log the review
        # responsible for the exit status, not only the successful fetch counts.
        print(json.dumps(dict(source_review=summary),indent=2))
        return 0 if all(q['status']=='complete' for q in reviewed.values()) else 1
    return 0 if all(v['status']=='complete' for v in result.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
