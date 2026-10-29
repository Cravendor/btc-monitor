"""Retrospective closed-native-candle 1H/4H diagnostic, no tuning."""
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
from scripts import elliott_history as history,multi_timeframe_signals as model
from scripts.market_scenarios import iso,time_ms

SPLIT=time_ms('2026-01-01T00:00:00+00:00')


def evaluate(rows,tf,horizon_hours):
    if tf not in ('1h','4h') or horizon_hours not in (24,168):raise ValueError('unsupported evaluation')
    period=history.PERIOD_MS[tf];steps=horizon_hours*3600000//period
    out=[];next_allowed=0
    for i in range(23,len(rows)-steps):
        segment=rows[i-23:i+steps+1]
        if any(b['open_time_ms']-a['open_time_ms']!=period for a,b in zip(segment,segment[1:])):continue
        start=rows[i]['open_time_ms']+period;end=start+horizon_hours*3600000
        if start<next_allowed or start<SPLIT<end:continue
        signal=model.assess(rows[i-23:i+1],tf,iso(start))
        if signal.get('status')!='provisional':continue
        change=(rows[i+steps]['close']/rows[i]['close']-1)*100
        out.append(dict(period='2026' if start>=SPLIT else '2025',grade=signal['grade'],change=change))
        next_allowed=end
    groups=defaultdict(list)
    for s in out:groups[(s['period'],s['grade'])].append(s['change'])
    g=[dict(period=k[0],grade=k[1],count=len(v),positive=sum(x>0 for x in v),negative=sum(x<0 for x in v),mean_return_pct=round(sum(v)/len(v),4)) for k,v in sorted(groups.items())]
    baseline=[]
    for period in sorted({s['period'] for s in out}):
        v=[s['change'] for s in out if s['period']==period]
        baseline.append(dict(period=period,count=len(v),positive=sum(x>0 for x in v),mean_return_pct=round(sum(v)/len(v),4)))
    return dict(horizon_hours=horizon_hours,groups=g,baseline=baseline)


def run(root='.',as_of=None):
    as_of=as_of or datetime.now(timezone.utc).isoformat()
    paths={tf:history.filename(Path(root)/history.DIRECTORY,tf) for tf in ('1h','4h')}
    initial={tf:path.read_bytes() for tf,path in paths.items()}
    sources=history.read(root,as_of)
    if any(path.read_bytes()!=initial[tf] for tf,path in paths.items()):raise ValueError('source_changed')
    review=sources['4h'].get('cross_timeframe_check',{})
    if review.get('mismatch_candles')!=0:raise ValueError('4h_hourly_source_conflict_or_unavailable')
    if any(sources[t].get('status') not in ('complete','partial') for t in ('1h','4h')):raise ValueError('source_unavailable')
    # Do not use an hourly window whose parent 4H coverage has a gap.
    ends=[time_ms(sources[t]['first_missing_at']) for t in ('1h','4h') if sources[t].get('first_missing_at')]
    cutoff=min(ends) if ends else time_ms(as_of)
    out=dict(as_of=as_of,market='Bitget BTCUSDT USDT-FUTURES',model='multi_tf_evidence_v0.2',
        source_scope='native candles; retrospective revised archive; not point-in-time',cutoff=iso(cutoff),
        cvd='unavailable_not_used',limitations=['no tuning','no trading or fees','2026 already explored; not independent holdout','samples are descriptive'],timeframes={})
    for tf in ('1h','4h'):
        path=paths[tf];before=initial[tf]
        rows=[r for r in sources[tf]['rows'] if r['open_time_ms']+history.PERIOD_MS[tf]<=cutoff]
        out['timeframes'][tf]=dict(source_sha256=hashlib.sha256(before).hexdigest(),source_status=sources[tf]['status'],
            candles=len(rows),closed_through=iso(rows[-1]['open_time_ms']+history.PERIOD_MS[tf]) if rows else None,
            results=[evaluate(rows,tf,24),evaluate(rows,tf,168)])
        if path.read_bytes()!=before:raise ValueError('source_changed')
    return out

if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2))
