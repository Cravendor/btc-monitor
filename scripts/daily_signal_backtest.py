"""Retrospective daily price/volume signal check; no model tuning or trading."""
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
from scripts import cycle_history as source,multi_timeframe_signals as model
from scripts.market_scenarios import iso,time_ms

SPLIT='2026-01-01T00:00:00+00:00'


def evaluate(rows, horizon_days):
    if horizon_days not in (1,7):raise ValueError('unsupported horizon')
    samples=[];next_allowed=0
    for i in range(23,len(rows)-horizon_days):
        segment=rows[i-23:i+horizon_days+1]
        if any(b['open_time_ms']-a['open_time_ms']!=source.DAY for a,b in zip(segment,segment[1:])):continue
        start=rows[i]['open_time_ms']+source.DAY;end=start+horizon_days*source.DAY
        if start<next_allowed:continue
        # No outcome may cross the development/holdout boundary.
        split=time_ms(SPLIT)
        if start<split<end:continue
        grade=model.assess(rows[i-23:i+1],'1d',iso(start))
        if grade.get('status')!='provisional':continue
        ret=rows[i+horizon_days]['close']/rows[i]['close']-1
        samples.append(dict(period='holdout_2026' if start>=split else 'development_2021_2025',grade=grade['grade'],return_pct=ret*100,start=iso(start),end=iso(end)))
        next_allowed=end
    groups=defaultdict(list)
    for s in samples:groups[(s['period'],s['grade'])].append(s['return_pct'])
    result=[]
    for (period,grade),v in sorted(groups.items()):
        result.append(dict(period=period,grade=grade,count=len(v),positive=sum(x>0 for x in v),negative=sum(x<0 for x in v),flat=sum(x==0 for x in v),mean_return_pct=round(sum(v)/len(v),4)))
    baselines=[]
    for period in sorted({s['period'] for s in samples}):
        v=[s['return_pct'] for s in samples if s['period']==period]
        baselines.append(dict(period=period,count=len(v),positive=sum(x>0 for x in v),mean_return_pct=round(sum(v)/len(v),4)))
    return dict(horizon_days=horizon_days,sampling='chronological_non_overlapping',groups=result,baseline=baselines,
                first= samples[0]['start'] if samples else None,last=samples[-1]['end'] if samples else None)


def run(path=source.PATH,as_of=None):
    as_of=as_of or datetime.now(timezone.utc).isoformat()
    raw=Path(path).read_bytes();boundary=time_ms(as_of)//source.DAY*source.DAY
    rows,_=source.load(path,boundary)
    if Path(path).read_bytes()!=raw:raise ValueError('source_changed')
    data=[rows[t] for t in sorted(rows)]
    return dict(model='multi_tf_evidence_v0.2',scope='Bitget BTCUSDT USDT-FUTURES daily price-volume only',
        source_sha256=hashlib.sha256(raw).hexdigest(),as_of=as_of,closed_through=iso(data[-1]['open_time_ms']+source.DAY) if data else None,
        limitations=['retrospective current archive; source revisions may be backdated','no CVD or other timeframes','no fees, trading results or calibrated probabilities','no parameter tuning','descriptive groups; small counts and dependence remain'],
        results=[evaluate(data,1),evaluate(data,7)])

if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2))
