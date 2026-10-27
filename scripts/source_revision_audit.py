"""Bounded public candle rechecks. Record differences; never activate revisions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile
from pathlib import Path
import time
from urllib.parse import urlencode
from scripts import cycle_history as daily, elliott_history as history
from scripts.enrich import BASE, request
from scripts.market_scenarios import time_ms, iso
from scripts.native_timeframe_candles import PERIOD_MS, GRANULARITIES

MODEL = 'bitget_closed_candle_revision_audit_v1'
TIMEFRAMES = ('1w','1d','4h','1h')
DIRECTORY = 'data/history/source-revision-audits'


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def source_rows(payload, tf, start, end):
    """Keep validated original seven fields; never arbitrary provider metadata."""
    rows = history.rows_from(payload,tf,end)
    if any(t<start-PERIOD_MS[tf] or t>=end for t in rows):
        raise ValueError('unexpected_source_window')
    if any(t not in rows for t in range(start,end,PERIOD_MS[tf])):
        raise ValueError('incomplete_source_window')
    raw = [list(r[:7]) for r in payload if int(r[0]) in rows]
    if len(raw)!=len(rows):
        raise ValueError('duplicate_source_rows')
    return dict(rows=rows,source_rows=raw)


def build(root='.', as_of=None, seconds=75, requester=request, clock=time.monotonic):
    as_of = as_of or datetime.now(timezone.utc).isoformat()
    now = time_ms(as_of)
    if type(seconds) is not int or not 16<=seconds<=90:
        raise ValueError('invalid_budget')
    deadline = clock()+seconds
    out = dict(schema_version=1,model_version=MODEL,exchange='bitget',
               market='USDT-FUTURES',symbol='BTCUSDT',as_of=as_of,
               comparison='exact_normalized_OHLCV',activation='none',checks=[])
    for tf in TIMEFRAMES:
        entry = dict(timeframe=tf,status='unavailable',reason='cache_unavailable',changes=[])
        out['checks'].append(entry)
        boundary = history.floor_time(now,tf)
        path = Path(root)/daily.PATH if tf=='1d' else history.filename(Path(root)/history.DIRECTORY,tf)
        try:
            # Identity/checksum validation precedes public requests or retention.
            original=path.read_bytes()
            rows,_ = daily.load(path,boundary) if tf=='1d' else history.load(path,tf,boundary)
            if path.read_bytes()!=original:
                raise ValueError('cache_changed_during_read')
            if len(rows)<2:
                raise ValueError('insufficient_cached_candles')
            selected = sorted(rows)[-2:]
            period = PERIOD_MS[tf]
            if selected[1]-selected[0]!=period:
                raise ValueError('noncontiguous_cached_tail')
            start,end = selected[0],selected[-1]+period
            entry.update(cache_sha256=hashlib.sha256(original).hexdigest(),
                         start=iso(start),end=iso(end),required_through=iso(boundary),
                         cache_tail_current=end==boundary,
                         cached_rows=[rows[t] for t in selected])
        except (OSError,ValueError,KeyError,TypeError,OverflowError):
            continue
        if clock()+15>deadline:
            entry['reason']='time_budget'
            continue
        url = BASE+'mix/market/history-candles?'+urlencode(dict(symbol='BTCUSDT',
              productType='USDT-FUTURES',granularity=GRANULARITIES[tf],
              startTime=start-period,endTime=end,limit=10))
        entry['url']=url
        try:
            result = requester(url,lambda payload:source_rows(payload,tf,start,end),True)
            observed = result['observed_at']
            if not now-60000<=time_ms(observed)<=now+seconds*1000+60000:
                raise ValueError('invalid_observation_time')
            entry['observed_at']=observed
            if result.get('status')!='ok':
                raise ValueError('source_unavailable')
            data = result['data']
            fresh = data['rows']
            # Check injected requester results too; only the six known fields
            # and closed, aligned times may enter an audit.
            fresh = {t:history.checked(c,tf,end) for t,c in fresh.items()}
            if any(t<start-period or t>=end or c['open_time_ms']!=t for t,c in fresh.items()):
                raise ValueError('unexpected_source_window')
            if any(t not in fresh for t in selected):
                raise ValueError('incomplete_source_window')
            raw = source_rows(data['source_rows'],tf,start,end)
            if raw['rows']!=fresh:
                raise ValueError('raw_normalized_disagreement')
            entry.update(observed_at=observed,source_rows=raw['source_rows'],
                         source_rows_sha256=digest(raw['source_rows']),
                         current_rows=[fresh[t] for t in selected])
            for t in selected:
                fields = {key:dict(cached=rows[t][key],current=fresh[t][key])
                          for key in daily.FIELDS if rows[t][key]!=fresh[t][key]}
                if fields:
                    entry['changes'].append(dict(opened_at=iso(t),fields=fields))
            entry.update(status='revision_detected' if entry['changes'] else 'unchanged_checked_window')
            entry.pop('reason',None)
        except (OSError,ValueError,KeyError,TypeError,OverflowError):
            entry['reason']='source_unavailable_or_invalid'
    out['status'] = ('revision_detected' if any(e['status']=='revision_detected' for e in out['checks'])
                     else 'unchanged_checked_windows' if all(e['status']=='unchanged_checked_window' for e in out['checks'])
                     else 'incomplete_audit')
    return out


def save_audit(root, audit):
    """Immutable content-addressed evidence; no overwrite or active-cache write."""
    if audit.get('model_version')!=MODEL or audit.get('activation')!='none':
        raise ValueError('invalid_audit_identity')
    stamp=datetime.fromtimestamp(time_ms(audit['as_of'])/1000,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder=Path(root)/DIRECTORY
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(stamp+'-'+digest(audit)+'.json')
    content=canonical(audit)+'\n'
    # Complete the file outside the published directory, then create its link
    # atomically without replacing an existing audit. A failed write/link must
    # not leave a partial JSON that the workflow would subsequently commit.
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False,
                                         dir=folder.parent,suffix='.tmp') as stream:
            temporary=Path(stream.name)
            stream.write(content)
        try:
            os.link(temporary,path)
        except FileExistsError:
            if path.read_text(encoding='utf-8')!=content:
                raise ValueError('audit_collision_or_tampering')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=75)
    args=parser.parse_args()
    audit=build(seconds=args.seconds)
    path=save_audit('.',audit)
    artifact=Path('output/source-revision-audit.json')
    artifact.parent.mkdir(parents=True,exist_ok=True)
    artifact.write_text(canonical(audit)+'\n',encoding='utf-8')
    print(canonical(dict(status=audit['status'],audit_path=path.as_posix(),
                         checks=[{k:v for k,v in e.items() if k in ('timeframe','status','reason','cache_tail_current','start','end')} for e in audit['checks']])))
    return 0 if audit['status']=='unchanged_checked_windows' else 1


if __name__=='__main__':
    raise SystemExit(main())
