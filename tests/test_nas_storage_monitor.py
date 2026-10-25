import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StorageMonitorTests(unittest.TestCase):
    def run_monitor(self, root, missing_db=False, report_is_directory=False,
                    failed_command=None, receipt_failure=False):
        root = Path(root)
        directory = root / 'cvd'
        directory.mkdir()
        if not missing_db:
            (directory / 'trades.sqlite3').write_bytes(b'original journal fixture')
        report = directory / 'storage-history.txt'
        if report_is_directory:
            report.mkdir()
        else:
            report.write_text('previous observation\n')
        env = dict(os.environ, BTC_CVD_DIR=str(directory), BTC_MONITOR_REPO=str(ROOT),
                   BTC_TASK_RECEIPTS=str(root / 'spool'), BTC_RECEIPT_PYTHON=sys.executable)
        if failed_command:
            binaries = root / 'bin'
            binaries.mkdir()
            stub = binaries / failed_command
            stub.write_text('#!/bin/sh\necho "inspection failed" >&2\nexit 1\n')
            stub.chmod(0o700)
            env['PATH'] = str(binaries) + os.pathsep + os.environ['PATH']
        if receipt_failure:
            env['BTC_TASK_RECEIPTS'] = str(root / 'blocked')
            (root / 'blocked').write_text('not a directory')
        result = subprocess.run(['/bin/sh', str(ROOT / 'nas/cvd_storage_monitor.sh')],
                                env=env, capture_output=True, text=True)
        receipts = [json.loads(p.read_text()) for p in (root / 'spool').glob('nas/storage/*.json')]
        return result, directory, receipts

    def test_preserves_history_and_journal_and_records_only_minimal_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            result, directory, receipts = self.run_monitor(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            history = (directory / 'storage-history.txt').read_text()
            self.assertTrue(history.startswith('previous observation\n==='))
            self.assertIn('trades.sqlite3', history)
            self.assertGreater(len(history.strip().splitlines()), 3)  # includes df output
            self.assertEqual((directory / 'trades.sqlite3').read_bytes(), b'original journal fixture')
            self.assertFalse((directory / 'storage-check.txt').exists())
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]['outcome'], 'completed')
            self.assertEqual(receipts[0]['task'], 'storage')
            self.assertEqual(set(receipts[0]), {'schema_version', 'source', 'task',
                                             'started_at', 'finished_at', 'outcome'})
            self.assertNotIn('original journal fixture', json.dumps(receipts))
            self.assertNotIn(str(directory), json.dumps(receipts))

    def test_missing_database_is_error_even_when_df_and_final_echo_succeed(self):
        with tempfile.TemporaryDirectory() as root:
            result, _, receipts = self.run_monitor(root, missing_db=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipts[0]['outcome'], 'error')

    def test_df_failure_is_error_even_when_final_echo_succeeds(self):
        with tempfile.TemporaryDirectory() as root:
            result, directory, receipts = self.run_monitor(root, failed_command='df')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipts[0]['outcome'], 'error')
            self.assertIn('inspection failed', (directory / 'storage-history.txt').read_text())

    def test_du_failure_is_error_even_when_later_inspections_succeed(self):
        with tempfile.TemporaryDirectory() as root:
            result, _, receipts = self.run_monitor(root, failed_command='du')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipts[0]['outcome'], 'error')

    def test_failed_history_append_records_error_without_touching_database(self):
        with tempfile.TemporaryDirectory() as root:
            result, directory, receipts = self.run_monitor(root, report_is_directory=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipts[0]['outcome'], 'error')
            self.assertEqual((directory / 'trades.sqlite3').read_bytes(), b'original journal fixture')

    def test_receipt_write_failure_is_nonzero_and_report_is_retained(self):
        with tempfile.TemporaryDirectory() as root:
            result, directory, receipts = self.run_monitor(root, receipt_failure=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('trades.sqlite3', (directory / 'storage-history.txt').read_text())
            self.assertEqual(receipts, [])
