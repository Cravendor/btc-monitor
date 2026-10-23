"""Periodic GitHub reserve for stale stored market snapshots, never a CVD host.

Run from a disposable Actions checkout of this public repository. GitHub writer
concurrency does not lock the NAS: fetch/recheck before collection and publication,
and always use a normal fast-forward push. Unknown races fail without overwrites.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.collector_health import check, run as write_health

ORIGINS = {
    'https://github.com/Cravendor/btc-monitor',
    'https://github.com/Cravendor/btc-monitor.git',
    'git@github.com:Cravendor/btc-monitor.git',
}
HISTORY = 'data/history/timeframe_signals.jsonl'
HEALTH = 'data/collector-health.json'
OUTPUTS = (HEALTH, 'data/latest.json', 'data/timeframe-health.json', HISTORY)


def recovery_required(report, event):
    return (event in ('schedule', 'workflow_dispatch') and
            report.get('status') in ('stale', 'missing'))


def git(*args, capture=False):
    result = subprocess.run(['git', *args], check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def remote_health():
    """Check actual upstream archive content, not an old checked_at report."""
    result = subprocess.run(['git', 'show', 'origin/main:' + HISTORY],
                            capture_output=True, text=True)
    rows = []
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            try:
                rows.append(json.loads(line))
            except (ValueError, TypeError):
                continue
    return check(rows, datetime.now(timezone.utc))


def publish_report(report, recovery):
    report['recovery'] = recovery
    Path(HEALTH).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


def run(event):
    if git('config', '--get', 'remote.origin.url', capture=True) not in ORIGINS:
        raise RuntimeError('Unexpected origin; reserve only supports Cravendor/btc-monitor.')
    if git('status', '--porcelain', capture=True):
        raise RuntimeError('Reserve requires a clean disposable checkout.')
    git('fetch', 'origin', 'main')
    git('merge', '--ff-only', 'origin/main')
    base = git('rev-parse', 'HEAD', capture=True)
    report = write_health()
    recovery = {
        'attempted': recovery_required(report, event), 'event': event,
        'before_status': report['status'], 'scope': 'periodic_market_snapshot_only',
        'outcome': 'not_needed' if report['status'] == 'current' else 'event_not_eligible',
    }
    failure = 0
    if recovery['attempted']:
        print('Stored snapshots stale/missing: testing reserve collector.', flush=True)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                   BTC_COLLECTOR_SOURCE='github_fallback')
        # No NAS access and no cached partial CVD values in a fallback snapshot.
        env.pop('BTC_CVD_DB', None)
        tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], env=env)
        if tests.returncode:
            failure = 1
            recovery['outcome'] = 'tests_failed'
        else:
            # Tests can take time: a restored NAS may have published meanwhile.
            git('fetch', 'origin', 'main')
            if git('rev-parse', 'origin/main', capture=True) != base:
                return changed_upstream()
            result = subprocess.run([sys.executable, 'scripts/collect.py'], env=env)
            failure = int(result.returncode != 0)
            try:
                snapshot_status = json.loads(Path('data/timeframe-health.json').read_text())['snapshot_status']
            except (OSError, ValueError, KeyError, TypeError):
                snapshot_status = 'missing'
            recovery.update(collection_exit_code=result.returncode, snapshot_status=snapshot_status)
            if failure or snapshot_status != 'ok':
                failure = 1
                recovery['outcome'] = 'incomplete_or_failed'
            else:
                recovery['outcome'] = 'uploaded'
        # Persist failure details and rechecked freshness before reporting failure.
        report = write_health()
    recovery['after_status'] = report['status']
    publish_report(report, recovery)

    # Prefer any newly restored upstream publisher. Never rebase generated feeds
    # over competing observations, reset a checkout, or force-push data.
    git('fetch', 'origin', 'main')
    if git('rev-parse', 'origin/main', capture=True) != base:
        return changed_upstream()
    paths = [path for path in (OUTPUTS if recovery['attempted'] else (HEALTH,))
             if Path(path).is_file()]
    if recovery['attempted']:
        paths.extend(str(path) for path in Path('data').glob('[0-9][0-9][0-9][0-9]') if path.is_dir())
    git('add', '--', *paths)
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode:
        message = ('Save GitHub reserve market snapshot and health' if recovery['attempted']
                   else 'Update BTC collector health')
        git('-c', 'user.name=github-actions[bot]',
            '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-m', message)
    git('push', 'origin', 'HEAD:main')
    print('Published watchdog report:', json.dumps(recovery), flush=True)
    return 1 if failure or report['status'] != 'current' else 0


def changed_upstream():
    report = remote_health()
    if report['status'] == 'current':
        print('Another publisher supplied fresh stored data; reserve upload skipped.', flush=True)
        return 0
    raise RuntimeError('Upstream changed but remains stale/missing; retry from a fresh checkout. No data overwritten.')


if __name__ == '__main__':
    try:
        sys.exit(run(os.environ.get('BTC_WATCHDOG_EVENT', '')))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Watchdog failed:', str(exc), file=sys.stderr)
        sys.exit(1)
