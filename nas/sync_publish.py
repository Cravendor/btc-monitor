"""Guarded NAS synchronization; caller must hold the publisher lock throughout."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import uuid

VIEWS = ['data/latest.json', 'data/timeframe-health.json', 'data/collector-health.json']
HISTORY = 'data/history/timeframe_signals.jsonl'
ORIGIN = 'git@github.com:Cravendor/btc-monitor.git'


def synchronize(repo, backup_dir, push=False, expected_origin=ORIGIN, attempts=3):
    repo, backup_dir = Path(repo).resolve(), Path(backup_dir).resolve()
    if backup_dir == repo or repo in backup_dir.parents:
        raise ValueError('Backup directory must be outside checkout')

    def git(*args, check=True):
        r = subprocess.run(['git', *args], cwd=str(repo), text=True, capture_output=True)
        if check and r.returncode:
            raise RuntimeError('Git ' + args[0] + ' failed: ' + r.stderr.strip())
        return r

    def read(*args):
        return git(*args).stdout.strip()

    def ancestor(a, b):
        r = git('merge-base', '--is-ancestor', a, b, check=False)
        if r.returncode not in (0, 1):
            raise RuntimeError('Cannot establish ancestry')
        return r.returncode == 0

    def rows(ref):
        result = {}
        for line in git('show', ref + ':' + HISTORY).stdout.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = row['updated_at']
            if not isinstance(key, str) or (key in result and result[key][0] != row):
                raise RuntimeError('Conflicting history identity')
            result[key] = (row, line)
        return result

    if read('config', '--get', 'remote.origin.url') != expected_origin:
        raise RuntimeError('Unexpected origin')
    if read('branch', '--show-current') != 'main' or read('status', '--porcelain'):
        raise RuntimeError('Clean main required; preserve and inspect')
    for marker in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD'):
        p = Path(read('rev-parse', '--git-path', marker))
        if (p if p.is_absolute() else repo / p).exists():
            raise RuntimeError('Another Git operation is active')

    for attempt in range(attempts if push else 1):
        git('fetch', 'origin', 'main')
        remote = read('rev-parse', 'origin/main')
        if ancestor('HEAD', remote):
            git('merge', '--ff-only', remote)
        elif not ancestor(remote, 'HEAD'):
            base = read('merge-base', 'HEAD', remote)
            # Local branch may contain only public observations, never code or logs.
            changes = git('diff', '--name-status', '--no-renames', base, 'HEAD').stdout.splitlines()
            immutable = {}
            archives = 0
            for line in changes:
                status, path = line.split('\t')
                if path in VIEWS + [HISTORY] and status == 'M':
                    continue
                archive = re.fullmatch(r'data/\d{4}/\d{2}/\d{2}/[A-Za-z0-9_-]+\.json', path)
                receipt = re.fullmatch(r'data/task-executions/nas/(watchdog|storage|startup)/\d{8}T\d{6}Z\.json', path)
                if status != 'A' or not (archive or receipt):
                    raise RuntimeError('Unexpected local changes; preserve and inspect')
                entry = read('ls-tree', 'HEAD', '--', path)
                if not entry.startswith('100644 blob '):
                    raise RuntimeError('Originals must be regular files')
                immutable[path] = read('rev-parse', 'HEAD:' + path)
                archives += bool(archive)
            if not archives:
                raise RuntimeError('No original NAS archive; preserve and inspect')
            combined = rows('HEAD')
            upstream = rows(remote)
            original = rows(base)
            for source in (combined, upstream):
                if any(key not in source or source[key][0] != value[0]
                       for key, value in original.items()):
                    raise RuntimeError('Original signal history rewritten')
            for key, value in upstream.items():
                if key in combined and combined[key][0] != value[0]:
                    raise RuntimeError('Conflicting original signal history')
                combined.setdefault(key, value)
            # Keep all three derived views together, from the newer observation.
            def observed(ref):
                value = json.loads(git('show', ref + ':data/latest.json').stdout)['finished_at']
                stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    raise ValueError('Aware observation time required')
                return stamp
            view_ref = 'HEAD' if observed('HEAD') > observed(remote) else remote
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / ('publish-' + uuid.uuid4().hex + '.bundle')
            git('bundle', 'create', str(backup), '--all')
            git('bundle', 'verify', str(backup))
            print('Verified publication backup:', backup, flush=True)
            try:
                r = git('merge', '--no-commit', '--no-ff', remote, check=False)
                if git('rev-parse', '--verify', 'MERGE_HEAD', check=False).returncode:
                    raise RuntimeError('Merge did not start')
                conflicts = set(read('diff', '--name-only', '--diff-filter=U').splitlines())
                if r.returncode not in (0, 1) or conflicts - set(VIEWS + [HISTORY]):
                    raise RuntimeError('Conflicting immutable files; preserve and inspect')
                git('checkout', view_ref, '--', *VIEWS)
                (repo / HISTORY).write_text('\n'.join(combined[k][1] for k in sorted(combined)) + '\n', encoding='utf-8')
                git('add', '--', HISTORY)
                for path, sha in immutable.items():
                    if read('rev-parse', ':' + path) != sha:
                        raise RuntimeError('Original observation changed')
                git('diff', '--cached', '--check')
                git('-c', 'user.name=BTC NAS collector', '-c', 'user.email=btc-nas@users.noreply.github.com',
                    'commit', '-m', 'Reconcile NAS observations with concurrent publication')
            except Exception:
                if not git('rev-parse', '--verify', 'MERGE_HEAD', check=False).returncode:
                    git('merge', '--abort')
                raise
        if not push:
            return
        if git('push', 'origin', 'HEAD:main', check=False).returncode == 0:
            return
        git('fetch', 'origin', 'main')
        if read('rev-parse', 'origin/main') == remote:
            raise RuntimeError('Push rejected without remote advancement; local commit retained')
    raise RuntimeError('Publication retry limit reached; all local commits retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--backup-dir', required=True)
    parser.add_argument('--push', action='store_true')
    args = parser.parse_args()
    synchronize(args.repo, args.backup_dir, args.push)
