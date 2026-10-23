import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.collect import collection_source
from scripts.collector_health import check
from scripts.watchdog_recovery import recovery_required
from scripts.timeframe_history_dashboard import collector_health_html

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'git@github.com:Cravendor/btc-monitor.git'


class RecoveryDecisionTests(unittest.TestCase):
    def test_event_matrix_prevents_collection_loops(self):
        for event in ('schedule', 'workflow_dispatch', 'workflow_run', 'push', 'pull_request', ''):
            for status in ('current', 'stale', 'missing', 'unknown', None):
                with self.subTest(event=event, status=status):
                    expected = event in ('schedule', 'workflow_dispatch') and status in ('stale', 'missing')
                    self.assertEqual(recovery_required({'status': status}, event), expected)

    def test_one_hour_boundary_future_and_malformed_archive_rows(self):
        now = datetime.now(timezone.utc)
        def row(age):
            return {'updated_at': (now-timedelta(seconds=age)).isoformat(), 'signals': {}}
        self.assertFalse(recovery_required(check([row(3600)], now), 'schedule'))
        self.assertTrue(recovery_required(check([row(3601)], now), 'schedule'))
        self.assertTrue(recovery_required(check([row(-60), None, {'signals': {}}], now), 'schedule'))

    def test_public_workflow_guards_and_shared_github_writer_group(self):
        workflow = (ROOT/'.github/workflows/collector-health.yml').read_text()
        for name in ('btc.yml', 'collector-health.yml', 'btc-4h-history-archive.yml'):
            self.assertIn('group: btc-market-collector', (ROOT/'.github/workflows'/name).read_text())
        self.assertIn('github.event.repository.private == false', workflow)
        self.assertIn('head_repository.full_name == github.repository', workflow)
        self.assertIn('timeout-minutes: 5', workflow)
        self.assertIn('BTC_WATCHDOG_EVENT: ${{ github.event_name }}', workflow)
        self.assertNotIn('actions: write', workflow)

    def test_collection_provenance_is_allowlisted(self):
        for source in ('nas', 'github_fallback', 'github_manual', 'local'):
            with patch.dict(os.environ, {'BTC_COLLECTOR_SOURCE': source}, clear=True):
                self.assertEqual(collection_source(), source)
        with patch.dict(os.environ, {'BTC_COLLECTOR_SOURCE': 'private-path', 'GITHUB_ACTIONS': 'true'}, clear=True):
            self.assertEqual(collection_source(), 'github_manual')
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(collection_source(), 'local')

    def test_dashboard_distinguishes_uploaded_incomplete_and_skipped_reserve(self):
        now = datetime.now(timezone.utc)
        report = check([{'updated_at': now.isoformat(), 'signals': {}}], now)
        report['recovery'] = {'attempted': True, 'outcome': 'uploaded',
                              'snapshot_status': 'ok', 'collection_exit_code': 0}
        self.assertIn('GESLAAGD', collector_health_html(report))
        for status in ('partial', 'missing', None):
            report['recovery']['snapshot_status'] = status
            self.assertIn('ONVOLLEDIG / MISLUKT', collector_health_html(report))
        report['recovery'] = {'attempted': False}
        self.assertIn('geen reservemeting', collector_health_html(report))
        report['recovery'] = {'attempted': '<script>alert(1)</script>'}
        self.assertNotIn('<script>alert(1)</script>', collector_health_html(report))


@unittest.skipUnless(shutil.which('git'), 'git required')
class RecoveryGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.remote = self.root/'remote.git'
        self.repo = self.root/'checkout'
        self.trace = self.root/'collection.json'
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT),
                        GIT_CONFIG_GLOBAL=str(self.root/'gitconfig'), GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
                        GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid',
                        BTC_WATCHDOG_EVENT='schedule', RECOVERY_TEST_TRACE=str(self.trace),
                        BTC_CVD_DB='/private/nas/should-not-be-read')
        for name in ('RECOVERY_TEST_OUTCOME', 'RECOVERY_TEST_RACE_REPO', 'RECOVERY_TEST_TEST_FAILURE'):
            self.env.pop(name, None)
        self.git('init', '--bare', str(self.remote))
        self.git('config', '--global', 'url.'+str(self.remote)+'.insteadOf', ORIGIN)
        self.git('clone', ORIGIN, str(self.repo))
        self.git('checkout', '-b', 'main', cwd=self.repo)
        (self.repo/'data/history').mkdir(parents=True)
        (self.repo/'scripts').mkdir()
        (self.repo/'tests').mkdir()
        self.history = self.repo/'data/history/timeframe_signals.jsonl'
        self.set_history(self.repo, 7200)
        for name in ('latest.json', 'timeframe-health.json', 'collector-health.json'):
            (self.repo/'data'/name).write_text('{}\n')
        # Network-free collector stand-in; all fetch/commit/push operations are real Git.
        (self.repo/'scripts/collect.py').write_text('''
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
Path(os.environ['RECOVERY_TEST_TRACE']).write_text(json.dumps({
  'source':os.environ.get('BTC_COLLECTOR_SOURCE'), 'cvd_db':os.environ.get('BTC_CVD_DB')}))
outcome=os.environ.get('RECOVERY_TEST_OUTCOME','ok')
if outcome=='exception': sys.exit(2)
stamp=datetime.now(timezone.utc).isoformat()
with Path('data/history/timeframe_signals.jsonl').open('a') as handle:
  handle.write(json.dumps({'updated_at':stamp,'signals':{}})+'\\n')
Path('data/latest.json').write_text(json.dumps({'reserve':True,'status':outcome}))
Path('data/timeframe-health.json').write_text(json.dumps({'snapshot_status':outcome}))
dated=Path('data/2026/10/23/reserve.json')
dated.parent.mkdir(parents=True,exist_ok=True)
dated.write_text(json.dumps({'status':outcome,'cvd_4h':{'status':'not_collected','value':None}}))
if os.environ.get('RECOVERY_TEST_RACE_REPO'):
  subprocess.run(['git','-C',os.environ['RECOVERY_TEST_RACE_REPO'],'push','origin','main'],check=True)
''')
        (self.repo/'tests/test_fake_runtime.py').write_text('''
import os, unittest
class RuntimeTests(unittest.TestCase):
    def test_runtime(self):
        self.assertFalse(os.environ.get('RECOVERY_TEST_TEST_FAILURE'))
''')
        self.git('add', '.', cwd=self.repo)
        self.git('commit', '-m', 'Initial stale data and test fixtures', cwd=self.repo)
        self.git('push', 'origin', 'main', cwd=self.repo)

    def git(self, *args, cwd=None):
        result = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def set_history(self, repo, age):
        path = repo/'data/history/timeframe_signals.jsonl'
        row = {'updated_at': (datetime.now(timezone.utc)-timedelta(seconds=age)).isoformat(), 'signals': {}}
        path.write_text(json.dumps(row)+'\n')

    def commit(self, message='Update'):
        self.git('add', '.', cwd=self.repo)
        self.git('commit', '-m', message, cwd=self.repo)
        self.git('push', 'origin', 'main', cwd=self.repo)

    def run_watchdog(self):
        return subprocess.run([sys.executable, '-m', 'scripts.watchdog_recovery'],
                              cwd=self.repo, env=self.env, text=True, capture_output=True)

    def remote_file(self, path):
        return self.git('--git-dir='+str(self.remote), 'show', 'main:'+path)

    def report(self):
        return json.loads(self.remote_file('data/collector-health.json'))

    def restored_nas(self):
        other = self.root/'restored-nas'
        self.git('clone', '-b', 'main', ORIGIN, str(other))
        self.set_history(other, 1)
        (other/'data/latest.json').write_text('{"nas":true}\n')
        self.git('add', '.', cwd=other)
        self.git('commit', '-m', 'Restored NAS snapshot', cwd=other)
        return other

    def test_fresh_data_only_updates_health_without_collection(self):
        self.set_history(self.repo, 10)
        self.commit()
        before = self.remote_file('data/latest.json')
        result = self.run_watchdog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.trace.exists())
        self.assertEqual(self.remote_file('data/latest.json'), before)
        self.assertFalse(self.report()['recovery']['attempted'])
        self.assertEqual(self.report()['status'], 'current')

    def test_stale_data_collects_commits_and_does_not_read_cvd(self):
        result = self.run_watchdog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.trace.read_text()), {'source': 'github_fallback', 'cvd_db': None})
        self.assertTrue(json.loads(self.remote_file('data/latest.json'))['reserve'])
        self.assertIsNone(json.loads(self.remote_file('data/2026/10/23/reserve.json'))['cvd_4h']['value'])
        self.assertEqual(self.report()['recovery']['outcome'], 'uploaded')
        self.assertEqual(self.report()['status'], 'current')
        self.assertEqual(self.git('status', '--porcelain', cwd=self.repo), '')

    def test_manual_check_can_recover_missing_history(self):
        self.history.write_text('not json\n')
        self.commit()
        self.env['BTC_WATCHDOG_EVENT'] = 'workflow_dispatch'
        result = self.run_watchdog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.report()['recovery']['before_status'], 'missing')
        self.assertTrue(self.report()['recovery']['attempted'])

    def test_post_collector_and_code_push_checks_never_collect(self):
        for event in ('workflow_run', 'push', ''):
            with self.subTest(event=event):
                self.env['BTC_WATCHDOG_EVENT'] = event
                result = self.run_watchdog()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.trace.exists())
                self.assertFalse(self.report()['recovery']['attempted'])
                self.assertEqual(self.report()['status'], 'stale')

    def test_partial_snapshot_is_uploaded_before_failure(self):
        self.env['RECOVERY_TEST_OUTCOME'] = 'partial'
        result = self.run_watchdog()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(self.remote_file('data/latest.json'))['status'], 'partial')
        self.assertEqual(self.report()['status'], 'current')
        self.assertEqual(self.report()['recovery']['outcome'], 'incomplete_or_failed')

    def test_collector_exception_and_failed_tests_save_failure_report(self):
        self.env['RECOVERY_TEST_OUTCOME'] = 'exception'
        result = self.run_watchdog()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.report()['recovery']['collection_exit_code'], 2)
        self.assertEqual(self.report()['status'], 'stale')
        self.env.pop('RECOVERY_TEST_OUTCOME')
        self.env['RECOVERY_TEST_TEST_FAILURE'] = '1'
        self.trace.unlink()
        result = self.run_watchdog()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.trace.exists())
        self.assertEqual(self.report()['recovery']['outcome'], 'tests_failed')

    def test_nas_upload_before_check_prevents_fallback(self):
        other = self.restored_nas()
        self.git('push', 'origin', 'main', cwd=other)
        result = self.run_watchdog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.trace.exists())
        self.assertTrue(json.loads(self.remote_file('data/latest.json'))['nas'])

    def test_nas_upload_during_collection_wins_without_rebase_or_overwrite(self):
        other = self.restored_nas()
        self.env['RECOVERY_TEST_RACE_REPO'] = str(other)
        result = self.run_watchdog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.trace.exists())
        self.assertIn('reserve upload skipped', result.stdout)
        self.assertTrue(json.loads(self.remote_file('data/latest.json'))['nas'])
        self.assertNotIn('reserve.json', self.git('--git-dir='+str(self.remote), 'ls-tree', '-r', '--name-only', 'main'))

    def test_push_rejection_preserves_remote_and_local_commit(self):
        before = self.git('--git-dir='+str(self.remote), 'rev-parse', 'main')
        hook = self.remote/'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o700)
        result = self.run_watchdog()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('--git-dir='+str(self.remote), 'rev-parse', 'main'), before)
        self.assertNotEqual(self.git('rev-parse', 'HEAD', cwd=self.repo), before)
        self.assertTrue((self.repo/'data/2026/10/23/reserve.json').is_file())

    def test_dirty_checkout_and_wrong_origin_fail_before_collection(self):
        marker = self.repo/'private-key'
        marker.write_text('test sentinel')
        self.assertNotEqual(self.run_watchdog().returncode, 0)
        marker.unlink()
        self.git('config', 'remote.origin.url', 'git@github.com:other/repo.git', cwd=self.repo)
        self.assertNotEqual(self.run_watchdog().returncode, 0)
        self.assertFalse(self.trace.exists())
