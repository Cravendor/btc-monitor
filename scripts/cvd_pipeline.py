"""NAS-only bounded recovery/verification before the ordinary market snapshot."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from scripts.cvd_backfill import audit, open_store, AuditError, WINDOW
from scripts.cvd_coverage import MARKETS, read_verified, read_diagnostics


def run(journal, store, now_ms=None, recover=audit, verify=read_verified):
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    end = now_ms // WINDOW * WINDOW
    result = dict(end_ms=end, status='partial', markets={})
    # Do not query a just-closed interval while the provider may still finalize it.
    if now_ms - end < 60000:
        result['reason'] = 'closed_interval_settlement_grace'
        return result
    db = open_store(store, journal)
    try:
        good = verify(store, journal, end, now_ms)
        if len(good) == 2:
            result.update(status='ok', verified_markets=sorted(good),
                          markets={m: 'verified_cached_evidence' for m in MARKETS})
            return result
        for market in MARKETS:
            if market in good:
                result['markets'][market] = 'verified_cached_evidence'
                continue
            rows = db.execute('SELECT run_id,report_json FROM cvd_backfill_runs '
                              'WHERE market=? AND end_ms=? ORDER BY rowid DESC', (market, end)).fetchall()
            resume = None
            for ident, payload in rows:
                candidate = json.loads(payload)
                if candidate.get('status') == 'incomplete' and candidate.get('reason') in (
                        'in_progress', 'network_storage_or_response_failure', 'network_timeout',
                        'network_error', 'http_500', 'http_502', 'http_503', 'http_504',
                        'time_budget_exhausted', 'page_budget_exhausted'):
                    resume = ident
                    break
                if candidate.get('status') == 'provider_consistent':
                    # A failed replay of completed evidence needs inspection, not refetch loops.
                    result['markets'][market] = 'completed_evidence_failed_validation'
                    break
            if market in result['markets']:
                continue
            try:
                report = recover(db, market, end_ms=end, now_ms=now_ms,
                                 resume=resume, seconds=180, max_pages=400)
                result['markets'][market] = report['status'] + ':' + report['reason']
            except (AuditError, OSError, ValueError) as exc:
                result['markets'][market] = 'recovery_failed:' + type(exc).__name__
        final = verify(store, journal, end, now_ms)
        result['verified_markets'] = sorted(final)
        result['diagnostics'] = read_diagnostics(store, end)
        if len(final) == 2:
            result['status'] = 'ok'
        return result
    finally:
        db.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--journal', required=True)
    p.add_argument('--store', required=True)
    args = p.parse_args()
    os.umask(0o077)
    lock_path = Path(args.store).resolve().with_suffix('.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run(args.journal, args.store)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
