from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from scripts import cvd_backfill as bf
from scripts.cvd_coverage import read_verified
from scripts.cvd_export import collect_cvd
from scripts.cvd_pipeline import run as pipeline


class CvdCoverageTests(unittest.TestCase):
    def test_direct_collector_import_exports_coverage_without_repository_on_path(self):
        for market in ('spot', 'usdt_futures'):
            self.candidate(market)
        code = '''import json, sys
from datetime import datetime, timezone
sys.path.insert(0, sys.argv[1])
from collect import collect_cvd
result = collect_cvd(path=sys.argv[2], backfill_path=sys.argv[3],
    now=datetime.fromtimestamp(int(sys.argv[4]) / 1000, timezone.utc))
print(json.dumps(result))
'''
        result = subprocess.run(
            [sys.executable, '-I', '-c', code,
             str(Path(__file__).resolve().parents[1] / 'scripts'),
             str(self.journal), str(self.store), str(self.now)],
            cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        exported = json.loads(result.stdout)
        self.assertTrue(exported['coverage_verified'])
        self.assertEqual(exported['status'], 'ok')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal, self.store = self.root / 'live.sqlite3', self.root / 'candidates.sqlite3'
        self.end = 2 * bf.WINDOW
        self.start, self.now = self.end - bf.WINDOW, self.end + 120000
        with sqlite3.connect(str(self.journal)) as db:
            db.executescript('''CREATE TABLE trades(market TEXT,trade_id TEXT,ts_ms INTEGER,
              received_ms INTEGER,price TEXT,size_btc TEXT,taker_side TEXT,
              PRIMARY KEY(market,trade_id));
              CREATE TABLE gaps(id INTEGER PRIMARY KEY,market,start_ms,end_ms,reason,resolved);
              INSERT INTO gaps VALUES(1,'spot',1,NULL,'legacy OPEN',0);''')
        self.db = bf.open_store(self.store, self.journal)
        self.addCleanup(self.db.close)

    def candidate(self, market, journal=True):
        rows = [dict(symbol='BTCUSDT',tradeId='3',ts=str(self.start + 1000),
                     price='100',size='.125',side='Buy'),
                dict(symbol='BTCUSDT',tradeId='2',ts=str(self.start + 2000),
                     price='100',size='.25',side='Sell')]
        if journal:
            with sqlite3.connect(str(self.journal)) as db:
                for row in rows:
                    db.execute('INSERT OR IGNORE INTO trades VALUES(?,?,?,?,?,?,?)',
                               (market,row['tradeId'],int(row['ts']),int(row['ts'])+1,
                                row['price'],row['size'],row['side'].lower()))
        pages = iter([rows, []])

        def fetch(path, query, timeout):
            data = ([[str(self.start),'100','100','100','100','.375','37.5']]
                    if path.endswith('history-candles') else next(pages))
            return dict(code='00000',data=data)

        result = bf.audit(self.db, market, self.end, now_ms=self.now,
                          fetch=fetch, pause=lambda _: None)
        self.assertEqual(result['status'], 'provider_consistent')
        return result

    def export(self, now=None):
        return collect_cvd(str(self.journal),
                           now=datetime.fromtimestamp((now or self.now)/1000, timezone.utc),
                           backfill_path=str(self.store))

    def test_complete_pair_replays_evidence_and_exports_scoped_values_read_only(self):
        for market in ('spot','usdt_futures'):
            self.candidate(market)
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.journal, self.store)]
        result = self.export()
        self.assertEqual(result['status'], 'ok')
        self.assertTrue(result['coverage_verified'])
        self.assertIsNone(result['value'])  # Never add spot and derivatives together.
        for market in ('spot','usdt_futures'):
            data = result['markets'][market]
            self.assertEqual(data['value'], '-0.125')
            self.assertEqual(data['coverage_scope'], 'bitget_public_history_only')
            self.assertEqual(data['side_semantics'], 'provider_reported_buy_sell')
            self.assertFalse(data['taker_side_verified'])
            self.assertEqual(data['trade_count'], 2)
        after = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.journal, self.store)]
        self.assertEqual(before, after)
        with sqlite3.connect(str(self.journal)) as db:
            self.assertEqual(db.execute('SELECT end_ms,resolved FROM gaps').fetchone(), (None,0))

    def test_one_market_does_not_confirm_the_other(self):
        self.candidate('spot')
        result = self.export()
        self.assertEqual(result['status'], 'partial')
        self.assertFalse(result['coverage_verified'])
        self.assertTrue(result['markets']['spot']['coverage_verified'])
        self.assertFalse(result['markets']['usdt_futures']['coverage_verified'])

    def test_old_or_future_interval_is_never_reused_as_current(self):
        self.candidate('spot')
        self.assertEqual(read_verified(self.store,self.journal,self.end+bf.WINDOW,
                                       self.now+bf.WINDOW), {})
        self.assertEqual(read_verified(self.store,self.journal,self.end,self.end-1), {})
        result = self.export(self.now + bf.WINDOW)
        self.assertFalse(result['coverage_verified'])
        self.assertIsNone(result['markets']['spot']['value'])

    def test_green_report_cannot_override_changed_page_hash_or_trade(self):
        for sql in ("UPDATE cvd_backfill_pages SET response_sha256='bad' WHERE run_id=?",
                    "UPDATE cvd_backfill_trades SET size_btc='100' WHERE run_id=?"):
            with self.subTest(sql=sql):
                report = self.candidate('spot')
                with self.db:
                    self.db.execute(sql, (report['run_id'],))
                # Remove older fixture runs so a different valid run cannot mask this corruption.
                with self.db:
                    self.db.execute('DELETE FROM cvd_backfill_runs WHERE run_id<>?', (report['run_id'],))
                self.assertEqual(read_verified(self.store,self.journal,self.end,self.now), {})

    def test_aggregate_and_candle_flags_are_recomputed(self):
        for key, value in [('candidate_delta_btc','10'), ('pages',99),
                           ('recovered_trades',99), ('status','incomplete'), ('market','wrong')]:
            with self.subTest(key=key):
                report = self.candidate('spot')
                report[key] = value
                with self.db:
                    self.db.execute('DELETE FROM cvd_backfill_runs WHERE run_id<>?', (report['run_id'],))
                    self.db.execute('UPDATE cvd_backfill_runs SET report_json=? WHERE run_id=?',
                                    (json.dumps(report),report['run_id']))
                self.assertEqual(read_verified(self.store,self.journal,self.end,self.now), {})

    def test_terminal_empty_page_is_required_even_with_matching_volumes(self):
        report = self.candidate('spot')
        with self.db:
            self.db.execute('DELETE FROM cvd_backfill_pages WHERE run_id=? AND row_count=0',
                            (report['run_id'],))
        self.assertEqual(read_verified(self.store,self.journal,self.end,self.now), {})

    def test_missing_journal_trades_are_covered_by_verified_history_not_inserted(self):
        self.candidate('spot', journal=False)
        verified = read_verified(self.store,self.journal,self.end,self.now)['spot']
        self.assertEqual(verified['recovered_missing_trades'], 2)
        self.assertEqual(verified['value'], '-0.125')
        with sqlite3.connect(str(self.journal)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM trades').fetchone()[0], 0)

    def test_new_journal_conflict_or_extra_trade_invalidates_saved_proof(self):
        self.candidate('spot')
        with sqlite3.connect(str(self.journal)) as db:
            db.execute("UPDATE trades SET size_btc='.5'")
        self.assertEqual(read_verified(self.store,self.journal,self.end,self.now), {})
        with sqlite3.connect(str(self.journal)) as db:
            db.execute('DELETE FROM trades')
            db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',
                       ('spot','extra',self.start+1,self.start+2,'100','.1','buy'))
        self.assertEqual(read_verified(self.store,self.journal,self.end,self.now), {})

    def test_unreadable_store_does_not_break_existing_partial_export(self):
        self.candidate('spot')
        result = collect_cvd(str(self.journal), datetime.fromtimestamp(self.now/1000,timezone.utc),
                             backfill_path=str(self.root/'missing.sqlite3'))
        self.assertEqual(result['markets']['spot']['observed_delta_btc'], '-0.125')
        self.assertFalse(result['coverage_verified'])

    def test_malformed_report_cannot_break_normal_market_export(self):
        report = self.candidate('spot')
        with self.db:
            self.db.execute('UPDATE cvd_backfill_runs SET report_json=? WHERE run_id=?',
                            ('[]',report['run_id']))
        result = self.export()
        self.assertFalse(result['coverage_verified'])
        self.assertEqual(result['markets']['spot']['observed_delta_btc'],'-0.125')

    def test_environment_candidates_are_used_only_by_nas_source(self):
        import os
        from unittest.mock import patch
        self.candidate('spot')
        for source, expected in [('github_fallback',False),('github_manual',False),('nas',True)]:
            with self.subTest(source=source), patch.dict(os.environ,{
                    'BTC_COLLECTOR_SOURCE':source,'BTC_CVD_BACKFILL_STORE':str(self.store)}):
                result = collect_cvd(str(self.journal),datetime.fromtimestamp(self.now/1000,timezone.utc))
                self.assertEqual(result['markets']['spot']['coverage_verified'],expected)

    def test_pipeline_uses_existing_pair_without_network_or_new_runs(self):
        for market in ('spot','usdt_futures'):
            self.candidate(market)
        result = pipeline(self.journal,self.store,self.now,
                          recover=lambda *a,**k:self.fail('no network needed'))
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM cvd_backfill_runs').fetchone()[0],2)

    def test_pipeline_grace_does_not_reuse_old_window_or_start_recovery(self):
        result = pipeline(self.journal,self.store,self.end+1000,
                          recover=lambda *a,**k:self.fail('settlement grace'))
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['reason'], 'closed_interval_settlement_grace')

    def test_pipeline_resumes_incomplete_market_and_continues_other_market_on_failure(self):
        report = bf.audit(self.db,'spot',self.end,now_ms=self.now,
                          fetch=lambda *a:(_ for _ in ()).throw(OSError()), pause=lambda _:None)
        # Use a known resumable network category, as produced by PR #50.
        report['reason'] = 'network_timeout'
        with self.db:
            self.db.execute('UPDATE cvd_backfill_runs SET report_json=? WHERE run_id=?',
                            (json.dumps(report),report['run_id']))
        calls = []

        def recover(db, market, **kwargs):
            calls.append((market,kwargs))
            return dict(status='incomplete',reason='network_timeout')

        result = pipeline(self.journal,self.store,self.now,recover=recover)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual([r[0] for r in calls], ['spot','usdt_futures'])
        self.assertEqual(calls[0][1]['resume'], report['run_id'])


if __name__ == '__main__':
    unittest.main()
