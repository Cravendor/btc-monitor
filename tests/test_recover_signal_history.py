import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from scripts.recover_signal_history import recover, run


class RecoveryTests(unittest.TestCase):
    before = datetime(2026, 10, 22, 18, tzinfo=timezone.utc)

    def snapshot(self):
        return {'exchange': 'bitget', 'market': 'USDT-FUTURES', 'symbol': 'BTCUSDT',
                'started_at': '2026-10-22T15:00:00Z', 'finished_at': '2026-10-22T15:01:00Z',
                'metrics': {'multi_timeframe': {'data': {'5m': {'status': 'ok',
                    'signal': {'status': 'provisional', 'grade': 'bullish',
                        'observed_at': '2026-10-22T15:00:00Z', 'model_version': 'v1'}}}}}}

    def test_original_labels_and_provenance_without_replayed_prices(self):
        row = recover(self.snapshot(), 'stored.json', self.before)
        self.assertEqual(row['signals']['5m']['grade'], 'bullish')
        self.assertIsNone(row['signals']['5m']['close_price'])
        self.assertEqual(row['provenance']['source'], 'stored.json')
        self.assertEqual(row['signals']['1h']['status'], 'unavailable')

    def test_identity_and_boundary(self):
        snapshot = self.snapshot()
        snapshot['exchange'] = 'other'
        self.assertIsNone(recover(snapshot, 'x', self.before))
        snapshot = self.snapshot()
        self.assertIsNone(recover(snapshot, 'x', datetime(2026, 10, 22, 15, 1, 30, tzinfo=timezone.utc)))

    def test_future_signal_is_not_recovered(self):
        snapshot = self.snapshot()
        snapshot['metrics']['multi_timeframe']['data']['5m']['signal']['observed_at'] = '2026-10-22T20:00:00Z'
        self.assertEqual(recover(snapshot, 'x', self.before)['signals']['5m']['status'], 'unavailable')

    def test_idempotent_preserves_existing_archive_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / '2026/10/22/old.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.snapshot()))
            archive = root / 'history.jsonl'
            original = json.dumps({'updated_at': self.before.isoformat(), 'signals': {}}) + '\n'
            archive.write_text(original)
            self.assertEqual(run(root, archive)['recovered_observations'], 1)
            after = archive.read_text()
            self.assertTrue(after.startswith(original))
            self.assertEqual(run(root, archive)['recovered_observations'], 0)
            self.assertEqual(archive.read_text(), after)
