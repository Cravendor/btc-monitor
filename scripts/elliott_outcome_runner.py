"""Bounded, prospective seven-day fixed-anchor outcomes from committed evidence."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from scripts import elliott_history as history
from scripts import elliott_observation_runner as observations
from scripts.elliott_observation_restore import reconstruct
from scripts.elliott_outcome_ledger import evaluate
from scripts.market_scenarios import iso,time_ms
from scripts.native_timeframe_candles import PERIOD_MS

MODEL='elliott_seven_day_outcome_v1'
DIRECTORY='data/history/elliott-outcomes'
HORIZON=7*24*60*60*1000
MAX_PER_RUN=4


def horizon(entry):
    tf=entry['timeframe'];observed=time_ms(entry['observed_at'])
    start=history.floor_time(observed,tf)
    if start<observed: start+=PERIOD_MS[tf]
    return start+HORIZON


def run(root='.',clock=lambda:datetime.now(timezone.utc)):
    root=Path(root);now=clock()
    if now.tzinfo is None: raise ValueError('aware_clock_required')
    now=now.astimezone(timezone.utc).isoformat()
    commit,refs=observations.committed_sources(root)
    data=history.read(root,now)
    if observations.committed_sources(root)!=(commit,refs):
        raise ValueError('sources_changed_during_evaluation')
    eligible,reason=observations._eligible(data,None,now)
    try:
        audit_bytes=(root/observations.AUDIT).read_bytes();audit=json.loads(audit_bytes)
    except (OSError,ValueError):
        audit_bytes=b'';audit={}
    if eligible and not observations.audit_eligible(audit,refs,now):
        eligible=False;reason='revision_audit_unavailable_or_changed'
    paths=observations._git(root,'ls-tree','-r','--name-only',commit,'--',observations.OUT).decode().splitlines()
    if len(paths)>100000: raise ValueError('observation_index_limit')
    pending=[]
    for name in paths:
        if not re.fullmatch(r'data/history/elliott-observations/(1w|1d|4h|1h)/[0-9]+-available\.json',name):
            continue
        try:
            raw=observations._git(root,'show',commit+':'+name)
            manifest=json.loads(raw)
            key=manifest.get('record_sha256')
            unsigned=dict(manifest);unsigned.pop('record_sha256',None)
            if (not isinstance(key,str) or not re.fullmatch(r'[0-9a-f]{64}',key) or
                hashlib.sha256(observations.canonical(unsigned).encode()).hexdigest()!=key or
                manifest.get('model_version')!=observations.MODEL or
                manifest.get('status')!='available' or
                manifest.get('timeframe')!=name.split('/')[-2] or
                time_ms(manifest['closed_through'])!=int(name.rsplit('/',1)[-1].split('-')[0]) or
                time_ms(manifest['observed_at'])<time_ms(manifest['closed_through'])):
                raise ValueError('invalid_manifest_identity')
            target=horizon(manifest)
            if target>time_ms(now):continue
            destination=root/DIRECTORY/manifest['timeframe']/(manifest['record_sha256']+'.json')
            if destination.exists():
                # Check stored event integrity even on repeated runs.
                prior=json.loads(destination.read_text());claimed=prior.pop('record_sha256',None)
                if claimed!=hashlib.sha256(observations.canonical(prior).encode()).hexdigest():
                    raise ValueError('existing_outcome_tampered')
                if prior.get('manifest_sha256')!=manifest['record_sha256']:
                    raise ValueError('existing_outcome_identity_conflict')
                continue
            pending.append((target,name,manifest,destination))
        except (KeyError,TypeError,ValueError,subprocess.CalledProcessError):
            raise ValueError('invalid_committed_observation')
    pending.sort(key=lambda x:(x[0],x[1]))
    result=dict(model_version=MODEL,run_at=now,source_commit=commit,
                eligible=eligible,reason=reason,pending=len(pending),written=[],errors=[])
    if not eligible:
        return result
    for target,name,manifest,destination in pending[:MAX_PER_RUN]:
        try:
            snapshot=reconstruct(root,manifest)
            # Evaluate only candles ending by the fixed horizon, never later price
            # action. Later sources are observed NOW, not backdated to target.
            outcome=evaluate(snapshot,data[manifest['timeframe']]['rows'],iso(target),'complete')
            record=dict(model_version=MODEL,timeframe=manifest['timeframe'],
                        status='evaluated',closed_through=iso(target),
                        manifest_path=name,manifest_sha256=manifest['record_sha256'],
                        original_observed_at=manifest['observed_at'],horizon_end=iso(target),
                        evaluated_at=now,later_source_commit=commit,later_source_sha256=refs,
                        revision_audit_sha256=hashlib.sha256(audit_bytes).hexdigest(),
                        evaluation=outcome,probability=None,wave_certification='unproven')
            if observations._put(destination,record):
                result['written'].append(destination.relative_to(root).as_posix())
        except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:
            result['errors'].append(dict(manifest_path=name,reason=str(exc)))
    return result


if __name__=='__main__':
    try:
        result=run();artifact=Path('output/elliott-outcome-current')
        for name in result['written']:
            target=artifact/Path(name).relative_to(DIRECTORY)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(name,target)
        artifact.mkdir(parents=True,exist_ok=True)
        (artifact/'run-status.json').write_text(observations.canonical(result)+'\n',encoding='utf-8')
        print(observations.canonical(result))
        if result['errors']: raise SystemExit(1)
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:
        print(json.dumps({'status':'error','reason':str(exc)}))
        raise SystemExit(1)
