"""Explicit one-off reconciliation of exactly one pending NAS snapshot; never force-push."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess

VIEWS = ['data/latest.json', 'data/timeframe-health.json', 'data/collector-health.json']
HISTORY = 'data/history/timeframe_signals.jsonl'
ORIGIN = 'git@github.com:Cravendor/btc-monitor.git'


def recover(repo, expected, archive, backup, expected_origin=ORIGIN):
    repo, backup = Path(repo).resolve(), Path(backup).resolve()
    def git(*args, check=True):
        result = subprocess.run(['git', *args], cwd=str(repo), text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode and check:
            raise RuntimeError('Git ' + args[0] + ' failed: ' + result.stderr.strip())
        return result
    def read(*args):
        return git(*args).stdout.strip()
    if not re.fullmatch(r'[0-9a-f]{40}', expected):
        raise ValueError('Full expected commit SHA required')
    if not re.fullmatch(r'data/\d{4}/\d{2}/\d{2}/[A-Za-z0-9_-]+\.json', archive):
        raise ValueError('Exact original dated snapshot path required')
    if repo == backup or repo in backup.parents or backup.exists():
        raise ValueError('New backup outside checkout required')
    if read('config', '--get', 'remote.origin.url') != expected_origin:
        raise RuntimeError('Unexpected origin')
    if read('branch', '--show-current') != 'main' or read('rev-parse', 'HEAD') != expected:
        raise RuntimeError('Branch/HEAD changed; obtain a new diagnosis')
    if read('status', '--porcelain'):
        raise RuntimeError('Uncommitted changes; preserve and inspect first')
    for marker in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD'):
        path = Path(read('rev-parse', '--git-path', marker))
        if (path if path.is_absolute() else repo / path).exists():
            raise RuntimeError('Another Git operation is active')
    changed = set(read('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines())
    required = set(VIEWS + [HISTORY, archive])
    receipts = changed - required
    if not required <= changed or any(not re.fullmatch(
            r'data/task-executions/nas/(watchdog|storage|startup)/\d{8}T\d{6}Z\.json',
            path) for path in receipts):
        raise RuntimeError('Unexpected local files; no merge attempted')
    for path in receipts:
        status = read('diff-tree', '--no-commit-id', '--name-status', '-r', 'HEAD', '--', path)
        entry = read('ls-tree', 'HEAD', '--', path)
        if status != 'A\t' + path or not entry.startswith('100644 blob '):
            raise RuntimeError('NAS receipts must be newly added regular files')
    immutable = {path: read('rev-parse', 'HEAD:' + path)
                 for path in [archive] + sorted(receipts)}
    git('bundle', 'create', str(backup), '--all')
    git('bundle', 'verify', str(backup))
    print('Verified backup:', backup, flush=True)
    git('fetch', 'origin', 'main')
    if read('rev-list', '--count', 'origin/main..HEAD') != '1':
        raise RuntimeError('Expected exactly one local commit; backup retained')
    entries = {}
    for ref in ('HEAD', 'origin/main'):
        for line in git('show', ref + ':' + HISTORY).stdout.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = row['updated_at']
            if not isinstance(key, str):
                raise ValueError('Invalid history identity')
            if key in entries and json.loads(entries[key]) != row:
                raise RuntimeError('Conflicting original history at the same timestamp')
            entries.setdefault(key, line)
    try:
        result = git('merge', '--no-commit', '--no-ff', 'origin/main', check=False)
        if git('rev-parse', '--verify', 'MERGE_HEAD', check=False).returncode:
            raise RuntimeError('Merge did not start')
        conflicts = set(read('diff', '--name-only', '--diff-filter=U').splitlines())
        if result.returncode not in (0, 1) or conflicts - set(VIEWS + [HISTORY]):
            raise RuntimeError('Unexpected merge conflict; preserve and inspect')
        git('checkout', 'origin/main', '--', *VIEWS)
        (repo / HISTORY).write_text('\n'.join(entries[k] for k in sorted(entries)) + '\n', encoding='utf-8')
        git('add', '--', HISTORY)
        if read('diff', '--name-only', '--diff-filter=U'):
            raise RuntimeError('Unresolved conflicts')
        for path, original in immutable.items():
            if read('rev-parse', ':' + path) != original:
                raise RuntimeError('Original NAS measurement or receipt changed')
        git('diff', '--cached', '--check')
        git('-c', 'user.name=BTC NAS collector', '-c', 'user.email=btc-nas@users.noreply.github.com',
            'commit', '-m', 'Preserve pending NAS observation and reconcile original signal history')
    except Exception:
        if not git('rev-parse', '--verify', 'MERGE_HEAD', check=False).returncode:
            git('merge', '--abort')
        raise
    # A concurrent remote push safely rejects this. Keep the merge and backup;
    # never repeat an old recovery or force-push to erase remote changes.
    git('push', 'origin', 'HEAD:main')
    print('Recovery pushed: original snapshot, both signal histories and '
          + str(len(receipts)) + ' NAS receipts preserved.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='/volume1/btc-monitor/repo')
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--backup', required=True)
    parser.add_argument('--lock', default='/volume1/btc-monitor/publish.lock')
    args = parser.parse_args()
    os.environ['GIT_TERMINAL_PROMPT'] = '0'
    with open(args.lock, 'a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        recover(args.repo, args.expected_head, args.archive, args.backup)
