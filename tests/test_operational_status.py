from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.operational_status import build, run

NOW = '2026-10-24T22:45:00Z'


def record(at='2026-10-24T22:40:00Z', source='nas', status='ok'):
    return dict(exchange='bitget', market='USDT-FUTURES', symbol='BTCUSDT', collection_source=source,
                finished_at=at, status=status, cvd_4h=dict(exchange='bitget', symbol='BTCUSDT', markets={
                    m: dict(exchange='bitget',symbol='BTCUSDT',market=m,latest_journal_trade_at='2026-10-24T22:39:59Z', journal_trade_status='recent')
                    for m in ('spot', 'usdt_futures')}))


class OperationalStatusTests(unittest.TestCase):
    def statuses(self, measurements, now=NOW, health=None):
        return {x['id']: x for x in build({'measurements': measurements}, health or {}, now)['items']}

    def test_recent_nas_upload_and_both_trade_sources_are_distinct_from_task_processes(self):
        r=self.statuses([record()])
        self.assertEqual(r['nas']['state'], 'good')
        self.assertEqual(r['cvd-spot']['state'], 'good')
        self.assertEqual(r['cvd-usdt_futures']['state'], 'good')
        for key in ('task-nas-watchdog', 'task-nas-storage', 'task-chatgpt-4h-warning'):
            self.assertEqual(r[key]['state'], 'unknown')

    def test_newer_reserve_cannot_turn_missing_or_old_nas_green(self):
        reserve=record('2026-10-24T22:44:00Z', 'github_reserve')
        self.assertEqual(self.statuses([reserve])['nas']['state'], 'unknown')
        r=self.statuses([reserve, record('2026-10-24T20:00:00Z')])
        self.assertEqual(r['nas']['state'], 'attention')
        self.assertNotIn('gestopt',r['nas']['label'].lower())

    def test_latest_failed_or_invalid_nas_cannot_be_replaced_by_an_older_success(self):
        for fault in ('error', 'partial', 'timestamp', 'market'):
            new=record('2026-10-24T22:44:00Z')
            if fault in ('error','partial'):new['status']=fault
            if fault=='timestamp':new['finished_at']='bad'
            if fault=='market':new['market']='SPOT'
            r=self.statuses([new,record()])
            self.assertNotEqual(r['nas']['state'],'good',fault)

    def test_invalid_future_empty_or_malformed_evidence_does_not_become_green(self):
        for value in ('2027-01-01T00:00:00Z','2026-10-24T22:40:00',None):
            r=self.statuses([record(value)])
            self.assertEqual(r['nas']['state'],'unknown')
            self.assertEqual(r['cvd-spot']['state'],'unknown')
        self.assertTrue(all(x['state']=='unknown' for x in build(None,None,NOW)['items']))

    def test_trade_recency_is_checked_independently_of_verified_closed_interval_cvd(self):
        m=record();m['cvd_4h']['status']='ok';m['cvd_4h']['coverage_verified']=True
        m['cvd_4h']['markets']['spot']['latest_journal_trade_at']='2026-10-24T20:00:00Z'
        m['cvd_4h']['markets']['usdt_futures']['latest_journal_trade_at']='2027-01-01T00:00:00Z'
        r=self.statuses([m])
        self.assertEqual(r['nas']['state'],'good')
        self.assertEqual(r['cvd-spot']['state'],'attention')
        self.assertEqual(r['cvd-usdt_futures']['state'],'unknown')

    def test_clock_alone_expires_green_proof_and_missing_health_is_unknown(self):
        r=self.statuses([record()],now='2026-10-24T23:26:00Z')
        self.assertEqual(r['nas']['state'],'attention')
        self.assertEqual(r['cvd-spot']['state'],'attention')
        self.assertEqual(r['snapshot-health']['state'],'unknown')
        health=dict(schema_version=3,status='current',checked_at='2026-10-24T22:44:00Z',last_snapshot_at='2026-10-24T20:00:00Z')
        self.assertEqual(self.statuses([record()],health=health)['snapshot-health']['state'],'attention')

    def test_public_output_contains_no_raw_metrics_logs_or_private_runtime_fields(self):
        m=record();m.update(pid=123,secret='private-test-value',path='/private/runtime')
        m['metrics']={'private':'never-published'}
        original=deepcopy(m)
        report=build({'measurements':[m]}, {}, NOW)
        serialized=json.dumps(report)
        for text in ('private-test-value','/private/runtime','never-published','latest_journal_trade_age_seconds'):
            self.assertNotIn(text,serialized)
        self.assertEqual(m,original)

    def test_wrong_journal_identity_and_health_contract_cannot_be_green(self):
        m=record();m['cvd_4h']['markets']['spot']['market']='usdt_futures'
        self.assertEqual(self.statuses([m])['cvd-spot']['state'],'unknown')
        m=record();m['cvd_4h']['exchange']='another_exchange'
        self.assertEqual(self.statuses([m])['cvd-usdt_futures']['state'],'unknown')
        health=dict(schema_version=999,status='current',checked_at='2026-10-24T22:44:00Z',last_snapshot_at='2026-10-24T22:40:00Z')
        self.assertEqual(self.statuses([record()],health=health)['snapshot-health']['state'],'unknown')

    def test_generator_handles_missing_files_without_false_success_and_copies_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            run(Path(tmp)/'absent.json',Path(tmp)/'absent-health.json',tmp,NOW)
            report=json.loads((Path(tmp)/'btc-status.json').read_text())
            self.assertTrue(all(x['state']=='unknown' for x in report['items']))
            for name in ('btc-status.html','status.mjs','status.css'):
                self.assertTrue((Path(tmp)/name).is_file())
