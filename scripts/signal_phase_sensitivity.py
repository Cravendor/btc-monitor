"""Retrospective sensitivity to non-overlapping sampling phases; no tuning."""
from collections import defaultdict
from datetime import datetime,timezone
from math import sqrt
import json
from scripts import intraday_signal_backtest as base,elliott_history as history,multi_timeframe_signals as model
from scripts.market_scenarios import time_ms,iso


def wilson(pos,n):
 if not n:return None
 z=1.95996398454;p=pos/n;den=1+z*z/n;centre=(p+z*z/(2*n))/den
 width=z*sqrt((p*(1-p)+z*z/(4*n))/n)/den
 return [round(max(0,centre-width),4),round(min(1,centre+width),4)]


def phases(rows,tf,hours,min_count=10):
 period=history.PERIOD_MS[tf];steps=hours*3600000//period
 if tf not in ('1h','4h') or hours not in (24,168) or min_count<1:raise ValueError('invalid parameters')
 groups=defaultdict(list)
 for i in range(23,len(rows)-steps):
  segment=rows[i-23:i+steps+1]
  if any(b['open_time_ms']-a['open_time_ms']!=period for a,b in zip(segment,segment[1:])):continue
  start=rows[i]['open_time_ms']+period
  if start<base.SPLIT:continue
  s=model.assess(rows[i-23:i+1],tf,iso(start))
  if s.get('status')!='provisional':continue
  phase=(start//period)%steps
  groups[(phase,s['grade'])].append(rows[i+steps]['close']/rows[i]['close']-1)
 output=[]
 for (phase,grade),v in sorted(groups.items()):
  n=len(v);pos=sum(x>0 for x in v)
  output.append(dict(phase=phase,grade=grade,count=n,positive=pos,
                     positive_rate=round(pos/n,4) if n>=min_count else None,
                     wilson_iid_approx=wilson(pos,n) if n>=min_count else None))
 summary=[]
 for grade in sorted({x['grade'] for x in output}):
  entries=[x for x in output if x['grade']==grade];valid=[x for x in entries if x['positive_rate'] is not None]
  summary.append(dict(grade=grade,phases_with_samples=len(entries),phases_meeting_minimum=len(valid),
                      min_positive_rate=min((x['positive_rate'] for x in valid),default=None),
                      max_positive_rate=max((x['positive_rate'] for x in valid),default=None),
                      min_count=min((x['count'] for x in entries),default=0),max_count=max((x['count'] for x in entries),default=0)))
 return dict(timeframe=tf,horizon_hours=hours,phase_count=steps,minimum_count=min_count,summary=summary,phases=output)


def run(root='.',as_of=None):
 as_of=as_of or datetime.now(timezone.utc).isoformat()
 validation=base.run(root,as_of);cutoff=time_ms(validation['cutoff']);data=history.read(root,as_of);out=[]
 for tf in ('1h','4h'):
  rows=[r for r in data[tf]['rows'] if r['open_time_ms']+history.PERIOD_MS[tf]<=cutoff]
  # Confirm source did not change between independent validated reads.
  import hashlib
  from pathlib import Path
  if hashlib.sha256((Path(root)/data[tf]['source_path']).read_bytes()).hexdigest()!=validation['timeframes'][tf]['source_sha256']:raise ValueError('source_changed')
  for h in (24,168):out.append(phases(rows,tf,h))
 return dict(as_of=as_of,cutoff=validation['cutoff'],source_hashes={tf:validation['timeframes'][tf]['source_sha256'] for tf in ('1h','4h')},
             scope='2026 retrospective; price-volume only; not independent holdout',results=out,
             caveats=['phases overlap each other and are not independent experiments','Wilson intervals assume independent Bernoulli observations; market dependence makes them approximate','no source revision point-in-time guarantee','small groups suppressed; no calibration or trading'])

if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2))
