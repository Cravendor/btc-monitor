import hashlib
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from scripts import elliott_observation_runner as runner
from scripts import elliott_observation_restore as restore
from scripts import elliott_outcome_ledger as ledger
from scripts.market_scenarios import iso
from tests.test_elliott_candidates import source,P


class RestoreTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.rows=source();ms=self.rows[-1]['open_time_ms']+P
        self.now=datetime.fromtimestamp(ms/1000,timezone.utc)
        data={tf:dict(status='complete',source_at=(self.now-timedelta(seconds=30)).isoformat(),rows=self.rows) for tf in runner.TIMEFRAMES}
        for tf in ('1w','1d','4h'):data[tf]['cross_timeframe_check']=dict(mismatch_candles=0,skipped_incomplete_groups=0)
        self.data=data
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        for f in restore.CODE:
            p=self.root/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path(f).read_bytes())
        for f in runner.SOURCES:
            p=self.root/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{"fixture":true}')
        checks=[dict(timeframe=tf,status='unchanged_checked_window',cache_tail_current=True,
                     cache_sha256=hashlib.sha256((self.root/f).read_bytes()).hexdigest(),
                     observed_at=(self.now-timedelta(seconds=10)).isoformat()) for tf,f in zip(runner.TIMEFRAMES,runner.SOURCES)]
        audit=dict(as_of=(self.now-timedelta(seconds=15)).isoformat(),status='unchanged_checked_windows',checks=checks)
        encoded=(ledger.canonical(audit)+'\n').encode();stamp=(self.now-timedelta(seconds=15)).strftime('%Y%m%dT%H%M%SZ')
        name=stamp+'-'+ledger.digest(audit)+'.json';path=self.root/restore.AUDIT_DIR/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
        out=self.root/runner.AUDIT;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(encoded)
        subprocess.run(['git','add','data','scripts'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=test','-c','user.email=test@example.com','commit','-qm','sources'],cwd=self.root,check=True)
        original_freeze=runner.freeze
        def make(rows,tf,now,state):
            if tf=='4h':return original_freeze(rows,tf,now,state)
            return dict(inventory={},rows_sha256='dummy')
        with patch.object(runner.history,'read',return_value=self.data),patch.object(runner,'freeze',side_effect=make):
            paths=runner.capture(self.root,clock=lambda:self.now)
        self.manifest=json.loads((self.root/next(x for x in paths if '/4h/' in x)).read_text())

    def restore(self,m):
        with patch.object(restore.history,'read',return_value=self.data):
            return restore.reconstruct(self.root,m)

    def sign(self,m):
        m.pop('record_sha256',None);m['record_sha256']=hashlib.sha256(ledger.canonical(m).encode()).hexdigest();return m

    def test_recreates_original_inventory_and_rows(self):
        original=self.restore(self.manifest)
        self.assertEqual(original['rows'],self.rows)
        self.assertEqual(original['inventory'],self.manifest['inventory'])
        self.assertEqual(original['rows_sha256'],self.manifest['rows_sha256'])

    def test_unavailable_tampered_changed_sources_and_code_are_blocked(self):
        m=dict(self.manifest,status='unavailable');self.sign(m)
        with self.assertRaises(ValueError):self.restore(m)
        m=dict(self.manifest,rows_sha256='bad')
        with self.assertRaises(ValueError):self.restore(m)
        m=dict(self.manifest,rows_sha256='bad');self.sign(m)
        with self.assertRaises(ValueError):self.restore(m)
        p=self.root/restore.CODE[0];p.write_text('changed')
        with self.assertRaisesRegex(ValueError,'historical_model_code_differs'):self.restore(self.manifest)

    def test_missing_original_commit_and_audit_never_guess(self):
        m=dict(self.manifest,source_commit='f'*40);self.sign(m)
        with self.assertRaisesRegex(ValueError,'pinned_git_object_unavailable'):self.restore(m)
        m=dict(self.manifest,revision_audit_sha256='0'*64);self.sign(m)
        with self.assertRaisesRegex(ValueError,'pinned_audit_missing_or_ineligible'):self.restore(m)
        refs=dict(self.manifest['source_sha256']);refs[runner.SOURCES[0]]='0'*64
        m=dict(self.manifest,source_sha256=refs);self.sign(m)
        with self.assertRaisesRegex(ValueError,'pinned_source_hash_mismatch'):self.restore(m)
        inventory=json.loads(json.dumps(self.manifest['inventory']))
        inventory['candidates'][0]['direction']='forged'
        m=dict(self.manifest,inventory=inventory);self.sign(m)
        with self.assertRaisesRegex(ValueError,'reconstructed_inventory_or_rows_mismatch'):self.restore(m)
