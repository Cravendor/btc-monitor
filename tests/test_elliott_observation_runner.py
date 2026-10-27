import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from scripts import elliott_observation_runner as runner

NOW=datetime(2026,10,27,17,30,tzinfo=timezone.utc)


def ready():
    q={tf:dict(status='complete',source_at='2026-10-27T17:00:00+00:00',rows=[{'x':1}]) for tf in runner.TIMEFRAMES}
    for tf in ('1w','1d','4h'):
        q[tf]['cross_timeframe_check']=dict(mismatch_candles=0,skipped_incomplete_groups=0)
    return q


class CaptureTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        for name in runner.SOURCES:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
        subprocess.run(['git','add','.'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=test','-c','user.email=test@example.com','commit','-qm','source'],cwd=self.root,check=True)
        checks=[]
        for tf,path in zip(runner.TIMEFRAMES,runner.SOURCES):
            checks.append(dict(timeframe=tf,status='unchanged_checked_window',cache_tail_current=True,
                               cache_sha256=hashlib.sha256((self.root/path).read_bytes()).hexdigest(),
                               observed_at='2026-10-27T17:29:30+00:00'))
        p=self.root/runner.AUDIT;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(dict(as_of='2026-10-27T17:29:00+00:00',status='unchanged_checked_windows',checks=checks)))

    def run_capture(self,data):
        with patch.object(runner.history,'read',return_value=data), patch.object(runner,'freeze',return_value={'inventory':{'candidates':[]},'rows_sha256':'abc'}):
            return runner.capture(self.root,clock=lambda:NOW)

    def test_capture_once_and_keep_original_after_later_retries(self):
        result=self.run_capture(ready());self.assertEqual(len(result),4)
        p=self.root/result[0];old=p.read_bytes()
        self.assertEqual(self.run_capture(ready()),[]);self.assertEqual(p.read_bytes(),old)
        obj=json.loads(old);self.assertEqual(obj['status'],'available')
        self.assertEqual(len(obj['source_commit']),40);self.assertEqual(len(obj['source_sha256']),4)
        self.assertIsNone(obj['probability'])

    def test_conflict_and_missing_cross_validation_never_capture_candidates(self):
        data=ready();data['4h']['status']='conflict'
        paths=self.run_capture(data);self.assertEqual(len(paths),4)
        for path in paths:
            o=json.loads((self.root/path).read_text());self.assertEqual(o['status'],'unavailable')
            self.assertNotIn('inventory',o)
        data=ready();data['1d']['cross_timeframe_check']['skipped_incomplete_groups']=1
        self.assertEqual(runner._eligible(data,None,NOW.isoformat())[0],False)
        # An eventual recovery can be retained separately for the same candle.
        self.assertEqual(len(self.run_capture(ready())),4)

    def test_uncommitted_source_or_tampered_existing_record_stops(self):
        paths=self.run_capture(ready());p=self.root/paths[0];p.write_text(p.read_text().replace('available','unavailable'))
        with self.assertRaises(ValueError):self.run_capture(ready())
        (self.root/runner.SOURCES[0]).write_text('{"changed":true}')
        with self.assertRaises(ValueError):self.run_capture(ready())

    def test_future_source_observation_is_not_accepted(self):
        data=ready();data['1h']['source_at']='2026-10-27T18:00:00+00:00'
        self.assertFalse(runner._eligible(data,None,NOW.isoformat())[0])

    def test_revision_audit_absent_changed_or_wrong_hash_blocks_capture(self):
        p=self.root/runner.AUDIT;a=json.loads(p.read_text())
        for variant in ('revision','wrong_hash','stale'):
            changed=json.loads(json.dumps(a))
            if variant=='revision': changed['status']='revision_detected'
            if variant=='wrong_hash': changed['checks'][0]['cache_sha256']='wrong'
            if variant=='stale': changed['as_of']='2026-10-27T16:00:00+00:00'
            p.write_text(json.dumps(changed))
            self.assertFalse(runner.audit_eligible(changed,runner.committed_sources(self.root)[1],NOW.isoformat()))
        p.unlink()
        paths=self.run_capture(ready())
        self.assertTrue(all(json.loads((self.root/x).read_text())['reason']=='revision_audit_unavailable_or_changed' for x in paths))
