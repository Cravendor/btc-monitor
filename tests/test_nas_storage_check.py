import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StorageCheckTests(unittest.TestCase):
    def run_check(self, root, with_db=True, dir_exists=True, extra_env=None):
        directory=Path(root)/'cvd'
        if dir_exists:directory.mkdir()
        if with_db:(directory/'trades.sqlite3').write_bytes(b'local database fixture')
        env=dict(os.environ, BTC_CVD_DIR=str(directory), BTC_MONITOR_REPO=str(ROOT),
                 BTC_TASK_RECEIPTS=str(Path(root)/'spool'), BTC_RECEIPT_PYTHON=sys.executable)
        env.update(extra_env or {})
        result=subprocess.run(['/bin/sh',str(ROOT/'nas/cvd_storage_check.sh')],env=env,capture_output=True,text=True)
        files=list((Path(root)/'spool').glob('nas/storage/*.json'))
        return result,directory,[json.loads(p.read_text()) for p in files]

    def test_success_saves_local_report_and_minimal_receipt_only(self):
        with tempfile.TemporaryDirectory() as root:
            result,directory,receipts=self.run_check(root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('DATABASEBESTANDEN',(directory/'storage-check.txt').read_text())
            self.assertEqual(len(receipts),1)
            self.assertEqual(receipts[0]['outcome'],'completed')
            self.assertEqual(receipts[0]['task'],'storage')
            self.assertEqual(set(receipts[0]),{'schema_version','source','task','started_at','finished_at','outcome'})
            self.assertNotIn('local database fixture',json.dumps(receipts))
            self.assertEqual((directory/'trades.sqlite3').read_bytes(),b'local database fixture')

    def test_missing_database_is_error_even_when_date_and_du_succeed(self):
        with tempfile.TemporaryDirectory() as root:
            result,directory,receipts=self.run_check(root,with_db=False)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(receipts[0]['outcome'],'error')
            self.assertIn('TIJDSTEMPEL',(directory/'storage-check.txt').read_text())

    def test_failed_report_redirection_is_error_not_green(self):
        with tempfile.TemporaryDirectory() as root:
            result,directory,receipts=self.run_check(root,with_db=False,dir_exists=False)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(receipts[0]['outcome'],'error')

    def test_receipt_failure_is_nonzero_without_removing_local_report(self):
        with tempfile.TemporaryDirectory() as root:
            result,directory,receipts=self.run_check(root,extra_env={'BTC_RECEIPT_PYTHON':'/absent/python'})
            self.assertNotEqual(result.returncode,0)
            self.assertTrue((directory/'storage-check.txt').exists())
            self.assertEqual(receipts,[])
