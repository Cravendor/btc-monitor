import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from scripts import cvd_backfill as backfill


class BackfillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = self.root / 'journal.sqlite3'
        with sqlite3.connect(str(self.journal)) as db:
            db.executescript('''CREATE TABLE trades(market TEXT,trade_id TEXT,ts_ms INTEGER,
              received_ms INTEGER,price TEXT,size_btc TEXT,taker_side TEXT,
              PRIMARY KEY(market,trade_id));
              CREATE TABLE gaps(id INTEGER PRIMARY KEY,market,start_ms,end_ms,reason,resolved);
              INSERT INTO gaps VALUES(1,'spot',1,NULL,'legacy OPEN',0);''')
        self.db = backfill.open_store(self.root / 'candidates.sqlite3', self.journal)
        self.addCleanup(self.db.close)
        self.end = backfill.WINDOW * 2
        self.start = self.end - backfill.WINDOW
        self.calls = []

    def row(self, ident='3', ts=None, size='0.125', side='Buy'):
        return dict(symbol='BTCUSDT', tradeId=ident, ts=str(self.start + 1000 if ts is None else ts),
                    price='100', size=size, side=side)

    def add_journal(self, row, market='spot', **changes):
        row = dict(row, **changes)
        with sqlite3.connect(str(self.journal)) as db:
            db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',
                       (market, row['tradeId'], int(row['ts']), int(row['ts']) + 1,
                        row['price'], row['size'], row['side'].lower()))

    def fetcher(self, pages, candle=None):
        pages = iter(copy.deepcopy(pages))
        candle = candle or [str(self.start), '100', '100', '100', '100', '0.375', '37.5']

        def fetch(path, query, timeout):
            self.calls.append((path, query, timeout))
            if path.endswith('history-candles'):
                return dict(code='00000', data=[candle])
            value = next(pages)
            if isinstance(value, Exception):
                raise value
            return dict(code='00000', data=value)
        return fetch

    def audit(self, pages, market='spot', candle=None, **kwargs):
        return backfill.audit(self.db, market, self.end, now_ms=self.end + 120000,
                              fetch=self.fetcher(pages, candle), pause=lambda _: None, **kwargs)

    def test_full_candidate_and_page_evidence_preserve_live_journal(self):
        first, second = self.row('3'), self.row('2', size='0.25', side='Sell')
        self.add_journal(first)
        before = hashlib.sha256(self.journal.read_bytes()).hexdigest()
        result = self.audit([[first], [second], []])
        self.assertEqual(result['status'], 'provider_consistent')
        self.assertEqual(result['candidate_delta_btc'], '-0.125')
        self.assertEqual(result['journal_missing'], 1)
        self.assertEqual(result['journal_extra'], 0)
        self.assertEqual(result['pages'], 3)
        self.assertFalse(result['coverage_verified'])
        self.assertIsNone(result['value'])
        # All three payloads, including terminal empty page, remain auditable locally.
        pages = self.db.execute('SELECT payload_json,response_sha256 FROM cvd_backfill_pages').fetchall()
        self.assertEqual(len(pages), 3)
        self.assertEqual(json.loads(pages[-1][0])['data'], [])
        for payload, digest in pages:
            self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(self.journal.read_bytes()).hexdigest(), before)
        with sqlite3.connect(str(self.journal)) as db:
            self.assertEqual(db.execute('SELECT end_ms,resolved FROM gaps').fetchone(), (None, 0))
        self.assertEqual(self.calls[0][1]['endTime'], str(self.end - 1))
        self.assertNotIn('idLessThan', self.calls[0][1])
        self.assertEqual(self.calls[1][1]['idLessThan'], '3')
        self.assertEqual(self.calls[-1][1]['endTime'], str(self.end))

    def test_short_page_requires_explicit_terminal_empty_page(self):
        result = self.audit([[self.row('3')], [self.row('2', size='0.25')]], max_pages=2)
        self.assertEqual(result['reason'], 'page_budget_exhausted')
        self.assertFalse(result['pagination_exhausted'])
        self.assertEqual(result['recovered_trades'], 2)
        self.assertIsNone(result['candidate_delta_btc'])

    def test_http_error_after_valid_page_keeps_recovered_candidates(self):
        result = self.audit([[self.row()], URLError('private-path-must-not-leak')])
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['recovered_trades'], 1)
        self.assertNotIn('private-path', json.dumps(result))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM cvd_backfill_trades').fetchone()[0], 1)
        stored = json.loads(self.db.execute('SELECT report_json FROM cvd_backfill_runs').fetchone()[0])
        self.assertEqual(stored['status'], 'incomplete')

    def test_cursor_repetition_and_non_descending_pages_fail_closed(self):
        for pages in ([[self.row('3')], [self.row('3')]],
                      [[self.row('2'), self.row('3')]],
                      [[self.row('3')], [self.row('4')]]):
            with self.subTest(pages=pages):
                result = self.audit(pages)
                self.assertEqual(result['reason'], 'cursor_or_order_violation')
                self.assertFalse(result['pagination_exhausted'])

    def test_trade_identity_and_interval_are_strict_and_page_is_atomic(self):
        cases = [dict(symbol='ETHUSDT'), dict(ts=str(self.start - 1)),
                 dict(ts=str(self.end)), dict(tradeId='03'), dict(tradeId=True),
                 dict(side='unknown'), dict(price='NaN'), dict(size='Infinity'),
                 dict(size='-1'), dict(ts=True)]
        for changes in cases:
            with self.subTest(changes=changes):
                result = self.audit([[self.row('4'), dict(self.row('3'), **changes)]])
                self.assertEqual(result['status'], 'incomplete')
                self.assertEqual(result['recovered_trades'], 0)
                self.assertEqual(self.db.execute('SELECT COUNT(*) FROM cvd_backfill_trades WHERE run_id=?',
                                                (result['run_id'],)).fetchone()[0], 0)

    def test_base_and_quote_candle_volumes_must_both_match_exactly(self):
        for base, quote in [('0.374999999999999999', '37.5'), ('0.375', '37.50000000001')]:
            with self.subTest(base=base, quote=quote):
                result = self.audit([[self.row('3'), self.row('2', size='0.25')], []],
                                    candle=[str(self.start), '100', '100', '100', '100', base, quote])
                self.assertEqual(result['reason'], 'candle_volume_mismatch')
                self.assertIsNone(result['candidate_delta_btc'])

    def test_missing_closed_candle_and_empty_interval_are_incomplete(self):
        result = self.audit([[self.row()], []],
                            candle=[str(self.end), '100', '100', '100', '100', '.125', '12.5'])
        self.assertEqual(result['reason'], 'closed_candle_missing_or_duplicated')
        result = self.audit([[]])
        self.assertEqual(result['reason'], 'empty_interval')

    def test_existing_trade_conflicts_are_not_overwritten(self):
        for change in [dict(price='101'), dict(size='0.126'), dict(side='sell'),
                       dict(ts=str(self.start + 9999))]:
            with self.subTest(change=change):
                ident = str(100 + len(self.calls))
                row = self.row(ident)
                self.add_journal(row, **change)
                result = self.audit([[row], []],
                                    candle=[str(self.start), '100', '100', '100', '100', '.125', '12.5'])
                self.assertEqual(result['reason'], 'journal_reconciliation_failed')
                self.assertGreater(result['journal_conflicts'], 0)

    def test_journal_only_trades_prevent_candidate_consistency(self):
        self.add_journal(self.row('99'))
        result = self.audit([[self.row('3'), self.row('2', size='0.25')], []])
        self.assertEqual(result['journal_extra'], 1)
        self.assertEqual(result['reason'], 'journal_reconciliation_failed')

    def test_spot_second_rounding_is_recorded_without_modifying_live_time(self):
        row = self.row('3', ts=self.start + 1000)
        self.add_journal(row, ts=str(self.start + 1999))
        result = self.audit([[row], []],
                            candle=[str(self.start), '100', '100', '100', '100', '.125', '12.5'])
        self.assertEqual(result['status'], 'provider_consistent')
        self.assertEqual(result['timestamp_rounding_matches'], 1)
        with sqlite3.connect(str(self.journal)) as db:
            self.assertEqual(db.execute('SELECT ts_ms FROM trades').fetchone()[0], self.start + 1999)

    def test_futures_never_uses_spot_timestamp_tolerance_or_spot_rows(self):
        row = self.row()
        self.add_journal(row)  # Spot row does not count as futures overlap.
        result = self.audit([[row], []], market='usdt_futures',
                            candle=[str(self.start), '100', '100', '100', '100', '.125', '12.5'])
        self.assertEqual(result['status'], 'provider_consistent')
        self.assertEqual(result['journal_missing'], 1)
        self.assertEqual(self.calls[0][1]['productType'], 'USDT-FUTURES')
        self.assertEqual(self.calls[-1][1]['granularity'], '4H')
        self.add_journal(row, market='usdt_futures', ts=str(self.start + 1999))
        result = self.audit([[row], []], market='usdt_futures',
                            candle=[str(self.start), '100', '100', '100', '100', '.125', '12.5'])
        self.assertEqual(result['reason'], 'journal_reconciliation_failed')

    def test_store_cannot_be_live_journal_hardlink_or_inside_repository(self):
        alias = self.root / 'alias.sqlite3'
        os.link(str(self.journal), str(alias))
        for path in (self.journal, alias, Path(backfill.__file__).parents[1] / 'should-not-exist.sqlite3'):
            with self.subTest(path=path), self.assertRaises(backfill.AuditError):
                backfill.open_store(path, self.journal)
        another = self.root / 'another-journal.sqlite3'
        with sqlite3.connect(str(another)) as db:
            db.execute('CREATE TABLE trades(x)')
        with self.assertRaises(backfill.AuditError):
            backfill.open_store(another, self.journal)
        with sqlite3.connect(str(another)) as db:
            self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(), [('trades',)])

    def test_attached_journal_is_read_only(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute('DELETE FROM journal.gaps')

    def test_soft_time_budget_exhaustion_is_not_success(self):
        clock = iter([0, 0, 2])
        result = self.audit([[self.row()]], seconds=1, clock=lambda: next(clock))
        self.assertEqual(result['reason'], 'time_budget_exhausted')
        self.assertEqual(result['recovered_trades'], 0)

    def test_invalid_interval_refuses_to_start_or_request(self):
        for end in (self.end + 1, self.end + backfill.WINDOW, -backfill.WINDOW):
            with self.subTest(end=end), self.assertRaises(backfill.AuditError):
                backfill.audit(self.db, 'spot', end, now_ms=self.end + 120000,
                               fetch=lambda *a: self.fail('must not request'))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM cvd_backfill_runs').fetchone()[0], 0)

    def test_separate_runs_keep_independent_rows(self):
        pages = [[self.row('3'), self.row('2', size='0.25')], []]
        a, b = self.audit(pages), self.audit(pages)
        self.assertNotEqual(a['run_id'], b['run_id'])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM cvd_backfill_trades').fetchone()[0], 4)

    def test_http_client_checks_fixed_endpoint_payload_limit_and_api_shape(self):
        from io import BytesIO
        path = '/api/v2/spot/market/fills-history'
        with patch('urllib.request.build_opener') as build:
            for payload in (b'{"code":"00000","data":[]}',
                            b'{"code":"429","data":[]}',
                            b'{"code":"00000","data":{}}', b'[]', b'x' * 1048577):
                build.return_value.open.return_value = BytesIO(payload)
                if payload == b'{"code":"00000","data":[]}':
                    self.assertEqual(backfill.request(path, {'symbol': 'BTCUSDT'}, 3)['data'], [])
                else:
                    with self.assertRaises(backfill.AuditError):
                        backfill.request(path, {'symbol': 'BTCUSDT'}, 3)
            self.assertIsNone(build.call_args[0][0]().redirect_request())
            build.reset_mock()
            with self.assertRaises(backfill.AuditError):
                backfill.request('/api/private', {}, 3)
            build.assert_not_called()


if __name__ == '__main__':
    unittest.main()
