import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.task_execution import read_items, validate, write_receipt
from scripts.operational_status import run

NOW = '2026-10-25T10:00:00Z'


def receipt(at='2026-10-25T09:59:00Z', outcome='completed'):
    return dict(schema_version=1, source='chatgpt', task='breaking-risk',
                started_at=None, finished_at=at, outcome=outcome)


class ReceiptTests(unittest.TestCase):
    def save(self, root, value, filename=None):
        filename = filename or value['finished_at'].replace('-', '').replace(':', '') + '.json'
        path = Path(root) / value['source'] / value['task'] / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def row(self, root, at=NOW):
        return next(r for r in read_items(root, at) if r['id'] == 'task-chatgpt-breaking-risk')

    def test_newer_error_wins_and_later_recovery_is_visible(self):
        with tempfile.TemporaryDirectory() as root:
            self.save(root, receipt('2026-10-25T08:00:00Z'))
            self.save(root, receipt('2026-10-25T09:00:00Z', 'error'))
            self.assertEqual(self.row(root)['state'], 'error')
            self.save(root, receipt())
            self.assertEqual(self.row(root)['state'], 'good')

    def test_elapsed_time_expires_success_but_never_erases_error(self):
        with tempfile.TemporaryDirectory() as root:
            self.save(root, receipt())
            self.assertEqual(self.row(root, '2026-10-25T14:00:00Z')['state'], 'attention')
            self.save(root, receipt('2026-10-25T10:00:00Z', 'error'))
            self.assertEqual(self.row(root, '2026-11-25T14:00:00Z')['state'], 'error')

    def test_malformed_newest_blocks_older_green_and_leaks_no_payload(self):
        with tempfile.TemporaryDirectory() as root:
            self.save(root, receipt('2026-10-25T08:00:00Z'))
            value = receipt(); value['private'] = 'never disclose this'
            self.save(root, value)
            self.assertEqual(self.row(root)['state'], 'unknown')
            self.assertNotIn('never disclose this', json.dumps(read_items(root, NOW)))

    def test_future_wrong_path_and_reversed_times_are_unknown(self):
        for change in ('future', 'path', 'reverse'):
            with tempfile.TemporaryDirectory() as root:
                value = receipt()
                filename = None
                if change == 'future': value['finished_at'] = '2027-01-01T00:00:00Z'
                if change == 'path': filename = '20261025T095800Z.json'
                if change == 'reverse': value['started_at'] = NOW
                self.save(root, value, filename)
                self.assertEqual(self.row(root)['state'], 'unknown')

    def test_timezone_schema_and_identity_are_required(self):
        for field, value in [('finished_at', '2026-10-25T09:59:00'), ('schema_version', True),
                             ('task', 'unrecognized'), ('outcome', 'running')]:
            data = receipt(); data[field] = value
            with self.assertRaises(ValueError): validate(data)

    def test_startup_receipt_never_claims_continuous_process_health(self):
        with tempfile.TemporaryDirectory() as root:
            value = receipt(); value.update(source='nas', task='startup')
            self.save(root, value)
            row = next(r for r in read_items(root, NOW) if r['id'] == 'task-nas-startup')
            self.assertEqual(row['state'], 'unknown')
            self.assertEqual(row['evidence_at'], value['finished_at'])

    def test_generated_page_reads_receipts_from_feed_folder(self):
        with tempfile.TemporaryDirectory() as root:
            self.save(Path(root) / 'task-executions', receipt())
            output = run(Path(root) / 'latest.json', Path(root) / 'health.json', Path(root) / 'site', NOW)
            self.assertEqual(next(x for x in output['items'] if x['id'] == 'task-chatgpt-breaking-risk')['state'], 'good')

    def test_writer_never_overwrites_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('scripts.task_execution.datetime') as clock:
                from datetime import datetime, timezone
                clock.now.return_value = datetime(2026, 10, 25, 10, tzinfo=timezone.utc)
                clock.fromisoformat.side_effect = datetime.fromisoformat
                path = write_receipt(root, 'watchdog', 'completed')
                before = path.read_text()
                with self.assertRaises(FileExistsError): write_receipt(root, 'watchdog', 'error')
                self.assertEqual(path.read_text(), before)
