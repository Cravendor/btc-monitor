"""Reconstruct an available manifest from its pinned, verified Git sources."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from scripts import elliott_history as history
from scripts import elliott_observation_runner as capture
from scripts.elliott_outcome_ledger import canonical, freeze
from scripts.market_scenarios import time_ms

CODE=('scripts/elliott_candidates.py','scripts/elliott_rules.py',
      'scripts/elliott_completion.py','scripts/elliott_history.py',
      'scripts/native_timeframe_candles.py','scripts/cycle_history.py',
      'scripts/market_scenarios.py','scripts/elliott_observation_runner.py')
AUDIT_DIR='data/history/source-revision-audits/'


def _show(root,commit,path):
    try:
        return capture._git(root,'show',commit+':'+path)
    except subprocess.CalledProcessError as exc:
        raise ValueError('pinned_git_object_unavailable') from exc


def reconstruct(root,manifest):
    """No live fetch or historical backfill. Reject changed or incomplete evidence."""
    if not isinstance(manifest,dict): raise ValueError('invalid_manifest')
    entry=dict(manifest);claimed=entry.pop('record_sha256',None)
    if claimed!=hashlib.sha256(canonical(entry).encode()).hexdigest():
        raise ValueError('manifest_hash_mismatch')
    if entry.get('model_version')!=capture.MODEL or entry.get('status')!='available':
        raise ValueError('manifest_not_available')
    tf=entry.get('timeframe');commit=entry.get('source_commit');observed=entry.get('observed_at')
    if tf not in capture.TIMEFRAMES or not isinstance(commit,str) or not re.fullmatch(r'[0-9a-f]{40}',commit):
        raise ValueError('invalid_manifest_identity')
    if entry.get('probability') is not None or entry.get('wave_certification')!='unproven':
        raise ValueError('unexpected_manifest_claim')
    if history.floor_time(time_ms(observed),tf)!=time_ms(entry['closed_through']):
        raise ValueError('manifest_boundary_mismatch')
    refs=entry.get('source_sha256')
    if not isinstance(refs,dict) or set(refs)!=set(capture.SOURCES):
        raise ValueError('source_reference_set_invalid')
    # Rebuilding with modified semantics would silently rewrite the as-of model.
    # Until a versioned runtime is provided, fail closed on any source-code drift.
    for path in CODE:
        if _show(root,commit,path)!=(Path(root)/path).read_bytes():
            raise ValueError('historical_model_code_differs')
    with tempfile.TemporaryDirectory() as folder:
        dest=Path(folder)
        for path in capture.SOURCES:
            raw=_show(root,commit,path)
            if hashlib.sha256(raw).hexdigest()!=refs[path]:
                raise ValueError('pinned_source_hash_mismatch')
            p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        state=history.read(dest,observed)
        ok,_=capture._eligible(state,tf,observed)
        if not ok or entry.get('source_states')!={t:state[t]['status'] for t in capture.TIMEFRAMES}:
            raise ValueError('pinned_source_no_longer_eligible')
        audit_hash=entry.get('revision_audit_sha256')
        if not isinstance(audit_hash,str) or not re.fullmatch(r'[0-9a-f]{64}',audit_hash):
            raise ValueError('audit_reference_invalid')
        try:
            names=capture._git(root,'ls-tree','-r','--name-only',commit,'--',AUDIT_DIR).decode().splitlines()
        except subprocess.CalledProcessError as exc:
            raise ValueError('pinned_git_object_unavailable') from exc
        if len(names)>10000: raise ValueError('audit_search_limit')
        audit=None
        for name in reversed(names):
            if not re.fullmatch(r'data/history/source-revision-audits/[0-9]{8}T[0-9]{6}Z-[0-9a-f]{64}\.json',name):
                continue
            raw=_show(root,commit,name)
            if hashlib.sha256(raw).hexdigest()==audit_hash:
                try: audit=json.loads(raw)
                except (ValueError,UnicodeDecodeError) as exc: raise ValueError('audit_invalid') from exc
                break
        if audit is None or not capture.audit_eligible(audit,refs,observed):
            raise ValueError('pinned_audit_missing_or_ineligible')
        snap=freeze(state[tf]['rows'],tf,observed,'complete')
        if (snap['rows_sha256']!=entry.get('rows_sha256') or
            snap['inventory']!=entry.get('inventory') or
            snap['closed_through']!=entry['closed_through']):
            raise ValueError('reconstructed_inventory_or_rows_mismatch')
        return snap
