import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'nas/collect_publish.sh'
ORIGIN = 'git@github.com:Cravendor/btc-monitor.git'


@unittest.skipUnless(shutil.which('git') and Path('/bin/flock').exists(), 'git and flock required')
class NasPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.remote = self.root / 'remote.git'
        self.repo = self.root / 'checkout'
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=str(self.root / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
        self.git('init', '--bare', str(self.remote))
        self.git('config', '--global', 'url.' + str(self.remote) + '.insteadOf', ORIGIN)
        self.git('clone', ORIGIN, str(self.repo))
        self.git('checkout', '-b', 'main', cwd=self.repo)
        (self.repo / 'data/history').mkdir(parents=True)
        for name in ('latest.json', 'timeframe-health.json', 'collector-health.json'):
            (self.repo / 'data' / name).write_text('{}\n')
        (self.repo / 'data/history/timeframe_signals.jsonl').write_text('')
        self.git('add', '.', cwd=self.repo)
        self.git('commit', '-m', 'Initial', cwd=self.repo)
        self.git('push', 'origin', 'main', cwd=self.repo)
        self.python = self.root / 'python-stub'
        # Stub only market calls and tests; use real git repositories and commits.
        self.python.write_text('''#!/bin/sh
case "$1" in
-c)
  if [ -n "${NAS_TEST_SSH_CAPTURE:-}" ]; then
    printf '%s' "$GIT_SSH_COMMAND" > "$NAS_TEST_SSH_CAPTURE"
  fi
  exit 0 ;;
-m) exit 0 ;;
scripts/collect.py)
  printf '{"snapshot_status":"%s"}\\n' "${NAS_TEST_STATUS:-ok}" > data/timeframe-health.json
  printf '{"nas":true}\\n' > data/latest.json
  mkdir -p data/2026/10/23
  printf '{"status":"ok"}\\n' > data/2026/10/23/test.json
  exit 0 ;;
-) [ "${NAS_TEST_STATUS:-ok}" = ok ]; exit $? ;;
esac
exit 9
''')
        self.python.chmod(0o700)
        self.env.update(BTC_REPO=str(self.repo), BTC_PYTHON=str(self.python), BTC_LOCK=str(self.root / 'lock'))

    def git(self, *args, cwd=None):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def run_task(self, mode='--run'):
        return subprocess.run(['/bin/sh', str(RUNNER), mode], env=self.env, capture_output=True, text=True)

    def test_read_only_check_does_not_commit_or_collect(self):
        before = self.git('rev-parse', 'HEAD', cwd=self.repo)
        result = self.run_task('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repo), before)
        self.assertEqual(json.loads((self.repo / 'data/latest.json').read_text()), {})

    def test_custom_key_and_known_hosts_configuration_is_preserved(self):
        expected = 'ssh -i /dedicated/key -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/dedicated/known_hosts'
        capture = self.root / 'ssh-capture'
        self.env.update(GIT_SSH_COMMAND=expected, NAS_TEST_SSH_CAPTURE=str(capture))
        result = self.run_task('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture.read_text(), expected)

    def test_default_ssh_is_noninteractive_and_time_limited(self):
        self.env.pop('GIT_SSH_COMMAND', None)
        capture = self.root / 'ssh-capture'
        self.env['NAS_TEST_SSH_CAPTURE'] = str(capture)
        result = self.run_task('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture.read_text(), 'ssh -o BatchMode=yes -o ConnectTimeout=15')

    def test_real_upload_and_partial_data_is_saved_before_failure(self):
        self.env['NAS_TEST_STATUS'] = 'partial'
        result = self.run_task()
        self.assertNotEqual(result.returncode, 0)
        remote = self.git('--git-dir=' + str(self.remote), 'show', 'main:data/timeframe-health.json')
        self.assertEqual(json.loads(remote)['snapshot_status'], 'partial')
        self.assertEqual(self.git('status', '--porcelain', cwd=self.repo), '')
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repo), self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main'))

    def test_dirty_checkout_and_unexpected_origin_refuse_collection(self):
        (self.repo / 'private-key').write_text('test sentinel, never upload')
        self.assertNotEqual(self.run_task().returncode, 0)
        (self.repo / 'private-key').unlink()
        self.git('remote', 'set-url', 'origin', 'git@github.com:another/repo.git', cwd=self.repo)
        self.assertNotEqual(self.run_task().returncode, 0)

    def test_conflict_preserves_local_observations_without_force_push(self):
        (self.repo / 'data/latest.json').write_text('{"local":true}\n')
        self.git('add', '.', cwd=self.repo)
        self.git('commit', '-m', 'Unpushed local observation', cwd=self.repo)
        local = self.git('rev-parse', 'HEAD', cwd=self.repo)
        other = self.root / 'other'
        self.git('clone', '-b', 'main', str(self.remote), str(other))
        (other / 'data/latest.json').write_text('{"remote":true}\n')
        self.git('add', '.', cwd=other)
        self.git('commit', '-m', 'Concurrent observation', cwd=other)
        self.git('push', 'origin', 'main', cwd=other)
        result = self.run_task()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repo), local)
        self.assertEqual(json.loads((self.repo / 'data/latest.json').read_text()), {'local': True})
        self.assertEqual(self.git('status', '--porcelain', cwd=self.repo), '')

    def test_successful_upload_and_retry_after_rejected_push(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o700)
        rejected = self.run_task()
        self.assertNotEqual(rejected.returncode, 0)
        pending = self.git('rev-parse', 'HEAD', cwd=self.repo)
        self.assertNotEqual(pending, self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main'))
        self.assertEqual(self.git('status', '--porcelain', cwd=self.repo), '')
        hook.unlink()
        retried = self.run_task()
        self.assertEqual(retried.returncode, 0, retried.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.repo), pending)
        self.assertEqual(self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main'), pending)
