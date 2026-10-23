import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from scripts.cvd_export import WINDOW_MS, collect_cvd


class CvdExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'trades.sqlite3'
        self.now = datetime(2026, 10, 23, 14, 22, tzinfo=timezone.utc)
        self.end = int(self.now.timestamp() * 1000) // WINDOW_MS * WINDOW_MS
        self.start = self.end - WINDOW_MS
        self.db = sqlite3.connect(str(self.path))
        self.addCleanup(self.db.close)
        # Exact schema supplied from the running NAS, including its primary key.
        self.db.executescript('''
            CREATE TABLE trades (market TEXT NOT NULL,trade_id TEXT NOT NULL,
              ts_ms INTEGER NOT NULL,received_ms INTEGER NOT NULL,price TEXT NOT NULL,
              size_btc TEXT NOT NULL,taker_side TEXT NOT NULL,
              PRIMARY KEY(market,trade_id));
            CREATE INDEX trades_by_window ON trades(market,ts_ms);
            CREATE TABLE gaps (id INTEGER PRIMARY KEY AUTOINCREMENT,market TEXT NOT NULL,
              start_ms INTEGER NOT NULL,end_ms INTEGER,reason TEXT NOT NULL,
              resolved INTEGER NOT NULL DEFAULT 0);
        ''')

    def trade(self, ident='1', market='spot', ts=None, size='0.1', side='buy'):
        ts = self.start if ts is None else ts
        self.db.execute('INSERT OR IGNORE INTO trades VALUES(?,?,?,?,?,?,?)',
                        (market, ident, ts, ts+1, '100', size, side))
        self.db.commit()

    def gap(self, start=None, end=None, resolved=0):
        self.db.execute('INSERT INTO gaps(market,start_ms,end_ms,reason,resolved) VALUES(?,?,?,?,?)',
                        ('spot', self.start if start is None else start, end, 'test', resolved))
        self.db.commit()

    def export(self):
        return collect_cvd(self.path, self.now)

    def test_decimal_sums_and_market_isolation(self):
        self.trade(size='0.123456789123456789')
        self.trade('2', size='0.023456789123456788', side='sell')
        self.trade(market='usdt_futures', size='2.5', side='sell')
        result = self.export()
        self.assertEqual(result['markets']['spot']['observed_delta_btc'], '0.100000000000000001')
        self.assertEqual(result['markets']['usdt_futures']['observed_delta_btc'], '-2.5')
        self.assertEqual(result['markets']['spot']['trade_count'], 2)
        self.assertIsNone(result['value'])
        self.assertFalse(result['coverage_verified'])

    def test_closed_utc_half_open_window_and_duplicate_replay(self):
        self.trade('before', ts=self.start-1, size='100')
        self.trade('start', ts=self.start, size='1')
        self.trade('start', ts=self.start, size='1')
        self.trade('last', ts=self.end-1, size='2')
        self.trade('end', ts=self.end, size='100')
        self.trade('open', ts=self.end+1, size='100')
        result = self.export()
        self.assertEqual(result['markets']['spot']['observed_delta_btc'], '3')
        self.assertEqual(result['markets']['spot']['trade_count'], 2)
        self.assertEqual(result['interval_start'], '2026-10-23T08:00:00+00:00')
        self.assertEqual(result['interval_end'], '2026-10-23T12:00:00+00:00')

    def test_legacy_open_gap_overlaps_but_is_never_repaired_by_export(self):
        self.trade()
        self.gap(self.start-WINDOW_MS)
        self.gap(self.start-100, self.start)
        self.gap(self.end, None)
        self.gap(self.start, self.end, resolved=1)
        self.gap(self.start+1, self.end-1)
        before = self.db.execute('SELECT * FROM gaps').fetchall()
        m = self.export()['markets']['spot']
        self.assertEqual(m['unresolved_overlapping_gaps'], 2)
        self.assertEqual(m['open_overlapping_gaps'], 1)
        self.assertEqual(before, self.db.execute('SELECT * FROM gaps').fetchall())

    def test_no_gaps_is_still_unverified_even_after_journal_recovers(self):
        self.trade()
        self.trade('recent', ts=int(self.now.timestamp()*1000)-1000)
        m = self.export()['markets']['spot']
        self.assertEqual(m['status'], 'partial')
        self.assertFalse(m['coverage_verified'])
        self.assertIsNone(m['value'])
        self.assertEqual(m['journal_trade_status'], 'recent')

    def test_empty_interval_is_missing_not_zero(self):
        self.trade(ts=self.end)
        m = self.export()['markets']['spot']
        self.assertEqual(m['status'], 'missing_data')
        self.assertIsNone(m['observed_delta_btc'])
        self.assertIsNone(m['observed_buy_btc'])
        self.assertEqual(m['trade_count'], 0)

    def test_observed_zero_is_distinct_from_missing(self):
        self.trade(size='1')
        self.trade('2', size='1', side='sell')
        m = self.export()['markets']['spot']
        self.assertEqual(m['observed_delta_btc'], '0')
        self.assertEqual(m['status'], 'partial')

    def test_invalid_trade_withholds_whole_market_but_keeps_other_market(self):
        for size in ('NaN', 'Infinity', '-1', '0', '1e999999', 'garbage'):
            with self.subTest(size=size):
                self.db.execute('DELETE FROM trades')
                self.trade(size=size)
                self.trade(market='usdt_futures')
                result = self.export()
                self.assertEqual(result['status'], 'invalid_data')
                self.assertIsNone(result['markets']['spot'].get('observed_delta_btc'))
                self.assertEqual(result['markets']['usdt_futures']['status'], 'partial')
                json.dumps(result, allow_nan=False)

    def test_invalid_side_or_timestamp_cannot_be_accepted(self):
        self.trade(side='unknown')
        self.assertEqual(self.export()['markets']['spot']['status'], 'invalid_data')
        self.db.execute('DELETE FROM trades')
        self.trade(ts=int(self.now.timestamp()*1000)+61000)
        self.assertEqual(self.export()['markets']['spot']['status'], 'invalid_data')

    def test_old_trades_are_not_proof_of_a_running_collector(self):
        self.trade()
        m = self.export()['markets']['spot']
        self.assertEqual(m['journal_trade_status'], 'stale')
        self.assertGreater(m['latest_journal_trade_age_seconds'], 300)
        self.assertIsNone(m['value'])

    def test_unconfigured_and_missing_path_do_not_create_database(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(collect_cvd(now=self.now)['status'], 'not_collected')
        missing = self.path.parent/'private-missing.sqlite3'
        result = collect_cvd(missing, self.now)
        self.assertEqual(result['status'], 'missing_data')
        self.assertFalse(missing.exists())
        self.assertNotIn(str(missing), json.dumps(result))

    def test_incompatible_or_corrupt_journal_fails_closed(self):
        for content in (b'not sqlite', b''):
            with self.subTest(content=content):
                other = self.path.parent/'invalid.sqlite3'
                other.write_bytes(content)
                self.assertEqual(collect_cvd(other, self.now)['status'], 'missing_data')

    def test_wal_reader_exports_committed_data_and_never_writes(self):
        self.db.execute('PRAGMA journal_mode=WAL')
        self.trade()
        self.db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',
                        ('spot','uncommitted',self.start, self.start,'100','10','buy'))
        before = self.path.read_bytes()
        result = self.export()
        self.assertEqual(result['markets']['spot']['observed_delta_btc'], '0.1')
        self.assertEqual(before, self.path.read_bytes())
        self.db.rollback()

    def test_boundary_time_and_naive_time(self):
        at_boundary = datetime.fromtimestamp(self.end/1000, timezone.utc)
        self.assertEqual(collect_cvd(self.path, at_boundary)['interval_end'], at_boundary.isoformat())
        with self.assertRaises(ValueError):
            collect_cvd(self.path, datetime(2026, 10, 23))
