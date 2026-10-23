import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from scripts.collector_health import check, recovery_required
from scripts.timeframe_history_dashboard import collector_health_html

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/collector-health.yml'


def run_block(name):
    lines = WORKFLOW.read_text().splitlines()
    start = lines.index('      - name: ' + name)
    begin = next(i for i in range(start, len(lines)) if lines[i] == '        run: |') + 1
    result = []
    for line in lines[begin:]:
        if line and not line.startswith('          '):
            break
        result.append(line[10:])
    return '\n'.join(result)


class RecoveryDecisionTests(unittest.TestCase):
    def test_event_matrix_prevents_retry_chains(self):
        for event in ('schedule', 'workflow_dispatch', 'workflow_run', 'push', 'pull_request', ''):
            for status in ('current', 'stale', 'missing', 'unknown', None):
                with self.subTest(event=event, status=status):
                    expected = event in ('schedule', 'workflow_dispatch') and status in ('stale', 'missing')
                    self.assertEqual(recovery_required({'status': status}, event), expected)

    def test_actual_freshness_boundary_and_invalid_future_rows(self):
        now = datetime.now(timezone.utc)
        def row(seconds):
            return {'updated_at': (now - timedelta(seconds=seconds)).isoformat(), 'signals': {}}
        self.assertFalse(recovery_required(check([row(3600)], now), 'schedule'))
        self.assertTrue(recovery_required(check([row(3601)], now), 'schedule'))
        self.assertTrue(recovery_required(check([row(-60)], now), 'schedule'))


class RecoveryWorkflowTests(unittest.TestCase):
    def test_fallback_shares_writer_lock_and_has_bounded_timeout(self):
        workflow = WORKFLOW.read_text()
        for path in ('btc.yml', 'btc-4h-history-archive.yml', 'collector-health.yml'):
            self.assertIn('group: btc-market-collector', (WORKFLOW.parent / path).read_text())
        self.assertIn('timeout-minutes: 3', workflow)
        self.assertIn("if: always() && steps.health.outcome == 'success'", workflow)

    def test_recheck_and_final_gate_for_success_partial_and_exception(self):
        for outcome, status, attempted, fresh, passes in (
            ('success', 'ok', True, True, True),
            ('success', 'partial', True, True, False),
            ('failure', '', True, False, False),
            ('failure', '', True, True, False),
            ('skipped', '', False, True, True),
            ('skipped', '', False, False, False),
        ):
            with self.subTest(outcome=outcome, status=status, fresh=fresh):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    history = root / 'data/history'
                    history.mkdir(parents=True)
                    now = datetime.now(timezone.utc) - timedelta(minutes=5 if fresh else 90)
                    (history / 'timeframe_signals.jsonl').write_text(json.dumps({'updated_at': now.isoformat(), 'signals': {}}) + '\n')
                    env = dict(os.environ, PYTHONPATH=str(ROOT), RECOVERY_NEEDED=str(attempted).lower(),
                               RECOVERY_OUTCOME=outcome, COLLECTION_STATUS=status, EVENT_NAME='schedule',
                               GITHUB_STEP_SUMMARY=str(root / 'summary'))
                    recheck = subprocess.run(['bash', '-e', '-c', run_block('Recheck freshness after fallback')], cwd=root, env=env, capture_output=True, text=True)
                    self.assertEqual(recheck.returncode, 0, recheck.stderr)
                    report = json.loads((root / 'data/collector-health.json').read_text())
                    self.assertEqual(report['recovery']['attempted'], attempted)
                    gate = subprocess.run(['bash', '-e', '-c', run_block('Flag stale or incomplete collection')], cwd=root, env=env, capture_output=True, text=True)
                    self.assertEqual(gate.returncode == 0, passes, gate.stderr)
                    if attempted:
                        rendered = collector_health_html(report)
                        self.assertIn('GESLAAGD' if passes else 'ONVOLLEDIG / MISLUKT', rendered)

    def test_decision_step_skips_fresh_and_post_collector_checks(self):
        for event, age, expected in [('schedule', 90, 'true'), ('schedule', 5, 'false'), ('workflow_run', 90, 'false'), ('workflow_dispatch', 90, 'true')]:
            with self.subTest(event=event, age=age):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    history = root / 'data/history'
                    history.mkdir(parents=True)
                    stamp = datetime.now(timezone.utc) - timedelta(minutes=age)
                    (history / 'timeframe_signals.jsonl').write_text(json.dumps({'updated_at': stamp.isoformat(), 'signals': {}}) + '\n')
                    env = dict(os.environ, PYTHONPATH=str(ROOT), EVENT_NAME=event, GITHUB_OUTPUT=str(root / 'outputs'))
                    result = subprocess.run(['bash', '-e', '-c', run_block('Check persisted snapshot freshness')], cwd=root, env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual((root / 'outputs').read_text().strip(), 'recover=' + expected)
