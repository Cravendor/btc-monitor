from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from scripts import elliott_outcome_runner as run
from scripts import elliott_observation_runner as obs
from scripts import elliott_outcome_ledger as ledger
from scripts.market_scenarios import iso
from tests.test_elliott_candidates import source,P


class OutcomeRunnerTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        self.old=source();boundary=self.old[-1]['open_time_ms']+P
        self.snapshot=ledger.freeze(self.old,'4h',iso(boundary+P//2),'complete')
        target=boundary+P+run.HORIZON
        self.now=datetime.fromtimestamp(target/1000,timezone.utc)
        self.rows=list(self.old)
        for i in range((target-boundary)//P):
            self.rows.append(dict(self.old[-1],open_time_ms=boundary+i*P))
        self.data={tf:dict(status='complete',source_at=(self.now-timedelta(seconds=30)).isoformat(),rows=self.rows) for tf in obs.TIMEFRAMES}
        for tf in ('1w','1d','4h'):
            self.data[tf]['cross_timeframe_check']=dict(mismatch_candles=0,skipped_incomplete_groups=0)
        for name in obs.SOURCES:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
        m=dict(model_version=obs.MODEL,status='available',timeframe='4h',closed_through=iso(boundary),
               observed_at=self.snapshot['observed_at'],probability=None,wave_certification='unproven')
        m['record_sha256']=hashlib.sha256(obs.canonical(m).encode()).hexdigest();self.manifest=m
        p=self.root/obs.OUT/'4h'/(str(boundary)+'-available.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(obs.canonical(m)+'\n')
        subprocess.run(['git','add','data'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=test','-c','user.email=test@example.com','commit','-qm','evidence'],cwd=self.root,check=True)
        checks=[]
        for tf,name in zip(obs.TIMEFRAMES,obs.SOURCES):
            checks.append(dict(timeframe=tf,status='unchanged_checked_window',cache_tail_current=True,
                               cache_sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest(),
                               observed_at=(self.now-timedelta(seconds=10)).isoformat()))
        p=self.root/obs.AUDIT;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(dict(as_of=(self.now-timedelta(seconds=20)).isoformat(),status='unchanged_checked_windows',checks=checks)))

    def run_once(self,data=None,now=None):
        with patch.object(run.history,'read',return_value=data or self.data),patch.object(run,'reconstruct',return_value=self.snapshot):
            return run.run(self.root,clock=lambda:now or self.now)

    def test_immutable_fixed_horizon_outcome_and_idempotence(self):
        result=self.run_once();self.assertEqual(len(result['written']),1);self.assertFalse(result['errors'])
        path=self.root/result['written'][0];record=json.loads(path.read_text())
        self.assertEqual(record['horizon_end'],self.now.isoformat())
        self.assertEqual(record['original_observed_at'],self.manifest['observed_at'])
        self.assertEqual(record['evaluation']['evaluation_model_version'],ledger.EVALUATION_MODEL)
        self.assertEqual(record['evaluation']['source_cutoff_at'],record['horizon_end'])
        self.assertIsNone(record['probability']);self.assertFalse(self.run_once()['written'])
        saved=path.read_text();path.write_text(saved.replace('evaluated','tampered'))
        with self.assertRaises(ValueError):self.run_once()

    def test_incomplete_source_and_future_horizon_do_not_produce_results(self):
        data=dict(self.data);data['4h']=dict(data['4h'],status='conflict')
        result=self.run_once(data=data);self.assertFalse(result['eligible']);self.assertFalse(result['written'])
        result=self.run_once(now=self.now-timedelta(hours=4));self.assertEqual(result['pending'],0)

    def test_changed_original_source_produces_error_not_false_outcome(self):
        rows=[dict(x) for x in self.rows];rows[0]['close']+=.01
        data=dict(self.data);data['4h']=dict(data['4h'],rows=rows)
        result=self.run_once(data=data);self.assertFalse(result['written'])
        self.assertIn('original_source_revision_or_missing_history',result['errors'][0]['reason'])
