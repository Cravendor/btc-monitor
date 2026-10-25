import json
from pathlib import Path
import tempfile
import unittest
from scripts.task_receipt_sync import sync


class ReceiptSyncTests(unittest.TestCase):
    def setup_paths(self, root):
        spool = Path(root) / 'spool'
        dest = Path(root) / 'repo'
        path = spool / 'nas/watchdog/20261025T100000Z.json'
        path.parent.mkdir(parents=True)
        value = dict(schema_version=1, source='nas', task='watchdog', started_at=None,
                     finished_at='2026-10-25T10:00:00Z', outcome='completed')
        path.write_text(json.dumps(value))
        return spool, dest, path, value

    def test_copy_keeps_spool_until_successful_push_acknowledgement(self):
        with tempfile.TemporaryDirectory() as root:
            spool, dest, path, value = self.setup_paths(root)
            self.assertEqual(sync(spool, dest), 1)
            self.assertTrue(path.exists())
            self.assertEqual(sync(spool, dest), 0)
            target = dest / path.relative_to(spool)
            self.assertEqual(json.loads(target.read_text()), value)
            sync(spool, dest, acknowledge=True)
            self.assertFalse(path.exists())
            self.assertTrue(target.exists())

    def test_new_receipt_arriving_after_import_is_not_acknowledged(self):
        with tempfile.TemporaryDirectory() as root:
            spool, dest, path, _ = self.setup_paths(root)
            sync(spool, dest, acknowledge=True)
            self.assertTrue(path.exists())

    def test_private_fields_wrong_identity_and_partial_write_stay_local(self):
        for kind in ('private', 'identity', 'partial'):
            with tempfile.TemporaryDirectory() as root:
                spool, dest, path, value = self.setup_paths(root)
                if kind == 'private': value['raw_log'] = 'private'
                if kind == 'identity': value['source'] = 'chatgpt'
                path.write_text('{' if kind == 'partial' else json.dumps(value))
                self.assertEqual(sync(spool, dest), 0)
                self.assertTrue(path.exists())
                self.assertFalse(dest.exists())

    def test_conflicting_immutable_receipt_is_never_overwritten_or_removed(self):
        with tempfile.TemporaryDirectory() as root:
            spool, dest, path, value = self.setup_paths(root)
            sync(spool, dest)
            value['outcome'] = 'error'
            path.write_text(json.dumps(value))
            sync(spool, dest)
            sync(spool, dest, acknowledge=True)
            self.assertTrue(path.exists())
            target = dest / path.relative_to(spool)
            self.assertEqual(json.loads(target.read_text())['outcome'], 'completed')

    def test_symlink_receipts_and_external_directories_are_not_imported(self):
        with tempfile.TemporaryDirectory() as root:
            spool, dest, path, value = self.setup_paths(root)
            outside = Path(root) / 'private.json'
            outside.write_text(json.dumps(value))
            path.unlink(); path.symlink_to(outside)
            self.assertEqual(sync(spool, dest), 0)
            self.assertTrue(outside.exists())

    def test_halfhour_upload_does_not_prematurely_expire_watchdog(self):
        from scripts.task_execution import read_items
        with tempfile.TemporaryDirectory() as root:
            spool, dest, path, value = self.setup_paths(root)
            row = lambda at: next(x for x in read_items(spool, at) if x['id'] == 'task-nas-watchdog')
            self.assertEqual(row('2026-10-25T10:31:00Z')['state'], 'good')
            self.assertEqual(row('2026-10-25T10:46:00Z')['state'], 'attention')
