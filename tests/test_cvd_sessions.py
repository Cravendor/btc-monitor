import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from scripts import bitget_cvd_collector as collector
from scripts import cvd_store as store
from scripts.cvd_export import collect_cvd


class SessionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'journal.sqlite3'
        self.db = store.connect(self.path)
        self.addCleanup(self.db.close)

    def start(self, market='spot', at=1000):
        session = store.begin_session(self.db, market, at)
        store.acknowledge(self.db, session, at + 10)
        return session

    def test_legacy_trades_and_open_markers_are_unchanged(self):
        # Exactly the original schema, without any new tables.
        legacy = Path(self.temp.name) / 'legacy.sqlite3'
        db = sqlite3.connect(str(legacy))
        db.executescript('''CREATE TABLE trades(market TEXT NOT NULL,trade_id TEXT NOT NULL,
          ts_ms INTEGER NOT NULL,received_ms INTEGER NOT NULL,price TEXT NOT NULL,
          size_btc TEXT NOT NULL,taker_side TEXT NOT NULL CHECK(taker_side IN ('buy','sell')),
          PRIMARY KEY(market,trade_id));
          CREATE TABLE gaps(id INTEGER PRIMARY KEY AUTOINCREMENT,market TEXT NOT NULL,
          start_ms INTEGER NOT NULL,end_ms INTEGER,reason TEXT NOT NULL,
          resolved INTEGER NOT NULL DEFAULT 0);
          INSERT INTO gaps(market,start_ms,reason) VALUES('spot',100,'legacy OPEN');
          INSERT INTO trades VALUES('spot','old',100,101,'100','0.2','buy');''')
        before_gap = db.execute('SELECT * FROM gaps').fetchall()
        before_trade = db.execute('SELECT * FROM trades').fetchall()
        db.close()
        db = store.connect(legacy)
        try:
            sid = store.begin_session(db, 'spot', 1000)
            store.acknowledge(db, sid, 1010)
            store.end_session(db, sid, 1020, 'test')
            self.assertEqual(db.execute('SELECT * FROM gaps WHERE id=1').fetchall(), before_gap)
            self.assertEqual(db.execute('SELECT * FROM trades').fetchall(), before_trade)
        finally:
            db.close()

    def test_reconnect_bounds_only_owned_outage_and_never_resolves(self):
        sid = self.start()
        store.record_frame(self.db, sid, 1050)
        store.end_session(self.db, sid, 1100, 'network')
        second = store.begin_session(self.db, 'spot', 1200)
        store.acknowledge(self.db, second, 1210)
        gaps = self.db.execute('SELECT start_ms,end_ms,resolved FROM gaps').fetchall()
        self.assertIn((1050, 1210, 0), gaps)
        self.assertTrue(all(end is not None and resolved == 0 for _, end, resolved in gaps))

    def test_atomic_batch_conflicting_duplicate_rolls_back_trades_and_checkpoint(self):
        sid = self.start()
        trade = ('1', 1020, '100', '.125', 'buy')
        store.record_frame(self.db, sid, 1030, [trade])
        store.record_frame(self.db, sid, 1040, [('1', 1020, '100.0', '0.1250', 'buy')])
        with self.assertRaises(ValueError):
            store.record_frame(self.db, sid, 1050, [
                ('2', 1045, '100', '0.5', 'sell'), ('1', 1020, '100', '0.2', 'buy')])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM trades').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT last_frame_ms,frame_count,inserted_trades,'
                         'duplicate_trades FROM cvd_sessions').fetchone(), (1040, 3, 1, 1))

    def test_invalid_decimal_and_future_trade_rollback_whole_frame(self):
        sid = self.start()
        for trade in [('bad', 1020, 'NaN', '1', 'buy'),
                      ('bad', 1020, '100', 'not-a-number', 'buy'),
                      ('bad', 1020, '100', '0', 'buy'),
                      ('bad', 62000, '100', '1', 'buy'),
                      ('bad', True, '100', '1', 'buy')]:
            with self.subTest(trade=trade), self.assertRaises(ValueError):
                store.record_frame(self.db, sid, 1030,
                                   [('good', 1020, '100', '1', 'sell'), trade])
            self.assertEqual(self.db.execute('SELECT COUNT(*) FROM trades').fetchone()[0], 0)

    def test_out_of_order_trades_keep_maximum_trade_checkpoint(self):
        sid = self.start()
        store.record_frame(self.db, sid, 1100, [('a', 1080, '100', '1', 'buy')])
        store.record_frame(self.db, sid, 1110, [('b', 1020, '100', '1', 'sell')])
        self.assertEqual(self.db.execute('SELECT last_trade_ms FROM cvd_sessions').fetchone()[0], 1080)

    def test_frames_require_ack_and_wall_clock_cannot_move_backwards(self):
        sid = store.begin_session(self.db, 'spot', 1000)
        with self.assertRaises(ValueError):
            store.record_frame(self.db, sid, 1010)
        store.acknowledge(self.db, sid, 1020)
        with self.assertRaises(ValueError):
            store.record_frame(self.db, sid, 1019)

    def test_market_sessions_and_acknowledgements_do_not_cross(self):
        spot = self.start()
        futures = store.begin_session(self.db, 'usdt_futures', 1000)
        store.end_session(self.db, spot, 1100, 'disconnected')
        store.acknowledge(self.db, futures, 1200)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM gaps WHERE market='spot' "
                                        'AND end_ms IS NULL').fetchone()[0], 1)

    def test_actual_process_crash_recovers_from_durable_checkpoint(self):
        code = '''import os,sys
from scripts import cvd_store as s
db=s.connect(sys.argv[1]); sid=s.begin_session(db,'spot',2000)
s.acknowledge(db,sid,2010)
s.record_frame(db,sid,2050,[('crash-trade',2040,'100','1','buy')])
os._exit(17)
'''
        result = subprocess.run([sys.executable, '-c', code, str(self.path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 17, result.stderr)
        sid = store.begin_session(self.db, 'spot', 9000)
        row = self.db.execute("SELECT state,ended_ms FROM cvd_sessions WHERE state='interrupted'").fetchone()
        self.assertEqual(row, ('interrupted', 2050))
        self.assertEqual(self.db.execute('SELECT start_ms,end_ms FROM gaps ORDER BY id DESC LIMIT 1')
                         .fetchone(), (2050, None))
        store.acknowledge(self.db, sid, 9010)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM trades WHERE trade_id='crash-trade'")
                         .fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT resolved FROM gaps ORDER BY id DESC LIMIT 1')
                         .fetchone()[0], 0)

    def test_health_never_equates_transport_to_verified_cvd(self):
        sid = self.start()
        store.record_frame(self.db, sid, 1030, [('a', 1020, '100', '1', 'buy')])
        health = store.export_health(self.db, Path(self.temp.name) / 'health.json')
        self.assertIsNone(health['cvd_4h'])
        self.assertFalse(health['markets']['spot']['coverage_verified'])
        self.assertEqual(health['markets']['spot']['transport_session']['state'], 'subscribed')
        # State is just the last durable checkpoint, never a live/complete claim.
        self.assertIsNone(health['markets']['usdt_futures']['transport_session'])
        exported = collect_cvd(str(self.path), now=datetime.fromtimestamp(18000, timezone.utc))
        self.assertEqual(exported['markets']['spot']['status'], 'partial')
        self.assertIsNone(exported['value'])
        self.assertFalse(exported['coverage_verified'])


class FakeTimeout(Exception):
    pass


class Socket:
    def __init__(self, frames, stop, clock):
        self.frames = iter(frames)
        self.stop, self.clock = stop, clock
        self.sent = []
        self.closed = False

    def settimeout(self, value):
        self.timeout = value

    def send(self, value):
        self.sent.append(value)

    def recv(self):
        item = next(self.frames, None)
        self.clock[0] += 5
        if item is None:
            self.stop.set()
            raise FakeTimeout()
        if isinstance(item, Exception):
            raise item
        return json.dumps(item) if isinstance(item, (dict, list)) else item

    def close(self):
        self.closed = True


class CollectorSessionTests(unittest.TestCase):
    ARG = {'instType': 'SPOT', 'channel': 'trade', 'instId': 'BTCUSDT'}

    def run_frames(self, frames):
        with tempfile.TemporaryDirectory() as directory:
            db = store.connect(Path(directory) / 'journal.sqlite3')
            stop, clock = threading.Event(), [1]
            ws = Socket(frames, stop, clock)
            client = type('Client', (), {'WebSocketTimeoutException': FakeTimeout,
                         'create_connection': staticmethod(lambda *a, **kw: ws)})
            with patch.object(collector.time, 'monotonic', side_effect=lambda: clock[0]), \
                    patch.object(collector, 'now_ms', side_effect=lambda: clock[0] * 1000):
                collector.run_attempt(client, db, 'SPOT', stop)
            rows = db.execute('SELECT trade_id FROM trades').fetchall()
            session = db.execute('SELECT state,end_reason,subscribed_ms,last_frame_ms,'
                                 'frame_count FROM cvd_sessions').fetchone()
            gaps = db.execute('SELECT start_ms,end_ms,resolved FROM gaps').fetchall()
            db.close()
            return ws, rows, session, gaps

    def ack(self):
        return {'event': 'subscribe', 'arg': self.ARG}

    def data(self):
        return {'action': 'update', 'arg': dict(self.ARG), 'data': [
            {'tradeId': 'a', 'ts': '1000', 'price': '100', 'size': '.125', 'side': 'buy'}]}

    def test_ack_valid_trade_pong_and_graceful_stop(self):
        ws, rows, session, gaps = self.run_frames([self.ack(), self.data(), 'pong'])
        self.assertTrue(ws.closed)
        self.assertEqual(rows, [('a',)])
        self.assertEqual(session[:2], ('stopped', 'stop requested'))
        self.assertEqual(session[4], 3)
        self.assertTrue(any(end is None for _, end, _ in gaps))

    def test_missing_ack_rejects_trades(self):
        _, rows, session, _ = self.run_frames([self.data()])
        self.assertEqual(rows, [])
        self.assertEqual(session[:2], ('disconnected', 'invalid frame or trade'))
        self.assertIsNone(session[2])

    def test_wrong_market_symbol_channel_ack_and_data_are_rejected(self):
        for field, wrong in [('instType', 'USDT-FUTURES'), ('instId', 'ETHUSDT'),
                             ('channel', 'ticker')]:
            for is_ack in (True, False):
                obj = self.ack() if is_ack else self.data()
                obj['arg'] = dict(obj['arg'], **{field: wrong})
                with self.subTest(field=field, ack=is_ack):
                    ws, rows, session, _ = self.run_frames([obj] if is_ack else [self.ack(), obj])
                    self.assertTrue(ws.closed)
                    self.assertEqual(rows, [])
                    self.assertEqual(session[1], 'invalid frame or trade')

    def test_malformed_messages_end_session_without_checkpointing_bad_frame(self):
        bad_trade = self.data()
        bad_trade['data'][0]['size'] = 'garbage'
        missing_id = self.data()
        del missing_id['data'][0]['tradeId']
        for frame in [b'binary', '', '{', [], {'event': 'error', 'msg': 'untrusted secret'},
                      bad_trade, missing_id, {'action': 'update', 'arg': self.ARG, 'data': {}}]:
            with self.subTest(frame=frame):
                ws, rows, session, _ = self.run_frames([self.ack(), frame])
                self.assertTrue(ws.closed)
                self.assertEqual(rows, [])
                self.assertEqual(session[1], 'invalid frame or trade')
                self.assertEqual(session[4], 1)
                self.assertNotIn('untrusted', session[1])

    def test_busy_feed_still_sends_application_ping(self):
        ws, _, session, _ = self.run_frames([self.ack()] + [self.data()] * 7)
        self.assertIn('ping', ws.sent)
        self.assertEqual(session[0], 'stopped')

    def test_pongs_without_ack_cannot_extend_subscription_deadline(self):
        ws, rows, session, _ = self.run_frames(['pong'] * 10)
        self.assertTrue(ws.closed)
        self.assertEqual(rows, [])
        self.assertEqual(session[1], 'connection or subscription timeout')
        self.assertIsNone(session[2])

    def test_idle_socket_times_out_and_retains_last_saved_frame(self):
        ws, _, session, _ = self.run_frames([self.ack()] + [FakeTimeout()] * 10)
        self.assertTrue(ws.closed)
        self.assertEqual(session[1], 'connection or subscription timeout')
        self.assertEqual(session[3], 6000)

    def test_connection_failure_is_persisted_even_without_socket(self):
        with tempfile.TemporaryDirectory() as directory:
            db = store.connect(Path(directory) / 'journal.sqlite3')
            client = type('Client', (), {'create_connection': staticmethod(
                lambda *a, **kw: (_ for _ in ()).throw(ConnectionError('failure')))})
            collector.run_attempt(client, db, 'USDT-FUTURES', threading.Event())
            self.assertEqual(db.execute('SELECT market,state,subscribed_ms FROM cvd_sessions')
                             .fetchone(), ('usdt_futures', 'disconnected', None))
            db.close()


if __name__ == '__main__':
    unittest.main()
