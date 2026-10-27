"""Capture first current Elliott inventory per native candle using committed sources."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from scripts import elliott_history as history
from scripts.elliott_outcome_ledger import freeze, canonical
from scripts.market_scenarios import time_ms, iso

MODEL='elliott_observation_manifest_v1'
TIMEFRAMES=('1w','1d','4h','1h')
SOURCES=('data/history/elliott/bitget_btcusdt_1w.json',
         'data/history/bitget_btcusdt_daily.json',
         'data/history/elliott/bitget_btcusdt_4h.json',
         'data/history/elliott/bitget_btcusdt_1h.json')
OUT='data/history/elliott-observations'
AUDIT='output/source-revision-audit.json'


def _git(root,*args):
    return subprocess.run(['git',*args],cwd=str(root),check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout


def committed_sources(root):
    """Pin all source files to the checked-out commit, refusing local changes."""
    commit=_git(root,'rev-parse','HEAD').decode().strip()
    refs={}
    for name in SOURCES:
        raw=(Path(root)/name).read_bytes()
        committed=_git(root,'show',commit+':'+name)
        if raw != committed:
            raise ValueError('source_not_identical_to_commit')
        refs[name]=hashlib.sha256(raw).hexdigest()
    return commit,refs


def _eligible(data,tf,now):
    # Require complete coverage on every linked scale. It is intentionally
    # conservative: a conflicting child or incomplete parent blocks capture.
    if any(data.get(t,{}).get('status')!='complete' for t in TIMEFRAMES):
        return False,'linked_source_incomplete_or_conflicted'
    for t in ('1w','1d','4h'):
        q=data[t].get('cross_timeframe_check',{})
        if q.get('mismatch_candles') != 0 or q.get('skipped_incomplete_groups') != 0:
            return False,'linked_source_not_reconciled'
    for t in TIMEFRAMES:
        observed=data[t].get('source_at')
        try:
            if not observed or time_ms(observed)>time_ms(now):
                return False,'source_time_invalid_or_future'
        except ValueError:
            return False,'source_time_invalid_or_future'
    return True,None


def audit_eligible(audit,refs,now):
    """Require the current bounded revision audit, not just local completeness."""
    try:
        age=time_ms(now)-time_ms(audit['as_of'])
        if not 0 <= age <= 600000 or audit['status']!='unchanged_checked_windows':
            return False
        checks={x['timeframe']:x for x in audit['checks']}
        if set(checks)!=set(TIMEFRAMES) or len(audit['checks'])!=len(TIMEFRAMES):
            return False
        paths=dict(zip(TIMEFRAMES,SOURCES))
        for tf in TIMEFRAMES:
            entry=checks[tf]
            if (entry.get('status')!='unchanged_checked_window' or
                entry.get('cache_tail_current') is not True or
                entry.get('cache_sha256')!=refs[paths[tf]] or
                time_ms(entry['observed_at'])>time_ms(now)):
                return False
        return True
    except (KeyError,ValueError,TypeError):
        return False


def _put(path,record):
    path.parent.mkdir(parents=True,exist_ok=True)
    record=dict(record,record_sha256=hashlib.sha256(canonical(record).encode()).hexdigest())
    raw=canonical(record)+'\n'; tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:
            tmp=Path(f.name);f.write(raw)
        try:
            os.link(tmp,path)
            return True
        except FileExistsError:
            old=json.loads(path.read_text(encoding='utf-8'))
            claimed=old.pop('record_sha256',None)
            if claimed != hashlib.sha256(canonical(old).encode()).hexdigest():
                raise ValueError('existing_observation_tampered')
            for k in ('model_version','timeframe','closed_through','status'):
                if old.get(k)!=record.get(k):
                    raise ValueError('observation_identity_conflict')
            return False
    finally:
        if tmp is not None: tmp.unlink(missing_ok=True)


def capture(root='.', clock=lambda: datetime.now(timezone.utc)):
    root=Path(root)
    instant=clock()
    if instant.tzinfo is None:
        raise ValueError('aware_clock_required')
    observed=instant.astimezone(timezone.utc).isoformat()
    commit,refs=committed_sources(root)
    data=history.read(root,observed)
    # Check sources again after parsing so the linked commit identifies the
    # exact source bytes used for candidate construction.
    if committed_sources(root)!=(commit,refs):
        raise ValueError('sources_changed_during_capture')
    valid,reason=_eligible(data,None,observed)
    try:
        audit_bytes=(root/AUDIT).read_bytes()
        audit=json.loads(audit_bytes)
    except (OSError,ValueError):
        audit_bytes=b'';audit={}
    if valid and not audit_eligible(audit,refs,observed):
        valid=False;reason='revision_audit_unavailable_or_changed'
    written=[]
    for tf in TIMEFRAMES:
        boundary=history.floor_time(time_ms(observed),tf)
        closed=iso(boundary)
        record=dict(model_version=MODEL,timeframe=tf,closed_through=closed,
                    observed_at=observed,source_commit=commit,source_sha256=refs,
                    revision_audit_sha256=hashlib.sha256(audit_bytes).hexdigest() if audit_bytes else None,
                    status='available' if valid else 'unavailable',reason=reason,
                    source_states={t:data.get(t,{}).get('status','unavailable') for t in TIMEFRAMES},
                    probability=None,wave_certification='unproven')
        if valid:
            snapshot=freeze(data[tf]['rows'],tf,observed,'complete')
            record.update(inventory=snapshot['inventory'],rows_sha256=snapshot['rows_sha256'])
        # One first available and one first unavailable record per closed period;
        # later retries never overwrite the first observation.
        path=root/OUT/tf/(str(boundary)+'-'+record['status']+'.json')
        if _put(path,record): written.append(path.relative_to(root).as_posix())
    return written


if __name__=='__main__':
    try:
        written=capture()
        artifact=Path('output/elliott-observation-current')
        for name in written:
            target=artifact/Path(name).relative_to(OUT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(name,target)
        print(json.dumps({'written':written}))
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:
        print(json.dumps({'status':'error','reason':str(exc)}))
        raise SystemExit(1)
