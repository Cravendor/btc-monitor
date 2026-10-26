import importlib.util
import json
from pathlib import Path
import shlex
import tempfile
import unittest
import test_nas_snapshot_recovery as fixtures

spec = importlib.util.spec_from_file_location('nas_sync', Path(__file__).parents[1] / 'nas/sync_publish.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SyncTests(unittest.TestCase):
    def setup(self, root, newer='local'):
        self.fixture = fixtures.RecoveryTests()
        self.git = self.fixture.git
        local, remote, head, archive = self.fixture.setup_repo(root)
        other = Path(root) / 'github'
        for folder, hour in ((local, '03' if newer == 'local' else '01'), (other, '02')):
            (folder / 'data/latest.json').write_text(json.dumps({'finished_at': '2026-10-26T'+hour+':00:00Z', 'source': folder.name}))
            self.git(folder, 'add', '.')
            if folder == local:
                self.git(folder, 'commit', '--amend', '--no-edit')
            else:
                self.git(folder, 'commit', '-m', 'Timestamped remote view')
        self.git(other, 'push')
        path, head = self.fixture.add_receipt(local)
        return local, remote, other, archive, path

    def test_both_view_orderings_preserve_originals_history_and_remote_code(self):
        for newer in ('local', 'remote'):
            with self.subTest(newer=newer), tempfile.TemporaryDirectory() as root:
                local, remote, other, archive, receipt = self.setup(root, newer)
                originals = {p: (local/p).read_bytes() for p in (archive, receipt)}
                module.synchronize(local, Path(root)/'backups', True, str(remote))
                for path, raw in originals.items():
                    self.assertEqual((local/path).read_bytes(), raw)
                self.assertEqual(json.loads((local/'data/latest.json').read_text())['source'], 'nas' if newer=='local' else 'github')
                self.assertEqual({json.loads(l)['updated_at'] for l in (local/module.HISTORY).read_text().splitlines()}, {'a','local','remote'})
                self.assertTrue((local/'new-code.py').exists())
                self.assertEqual(self.git(local,'rev-parse','HEAD'),self.git(remote,'rev-parse','main'))
                self.assertEqual(len(list((Path(root)/'backups').glob('*.bundle'))), 1)

    def test_rejection_retains_merge_and_next_run_can_publish_it(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, other, archive, receipt = self.setup(root)
            hook=remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o700)
            with self.assertRaisesRegex(RuntimeError, 'without remote advancement'):
                module.synchronize(local, Path(root)/'backups', True, str(remote))
            pending=self.git(local,'rev-parse','HEAD')
            self.assertEqual(self.git(local,'status','--porcelain'), '')
            hook.unlink()
            module.synchronize(local, Path(root)/'backups', True, str(remote))
            self.assertEqual(self.git(remote,'rev-parse','main'),pending)

    def test_actual_remote_race_is_retried_without_recollection(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, other, archive, receipt = self.setup(root)
            marker=Path(root)/'ran'
            hook=local/'.git/hooks/pre-push'
            hook.write_text('#!/bin/sh\nset -e\nif [ ! -e '+shlex.quote(str(marker))+' ]; then\n'
                'touch '+shlex.quote(str(marker))+'\n'
                'git -C '+shlex.quote(str(other))+' commit --allow-empty -m race\n'
                'git -C '+shlex.quote(str(other))+' push origin main\nfi\n')
            hook.chmod(0o700)
            module.synchronize(local, Path(root)/'backups', True, str(remote))
            self.assertTrue(marker.exists())
            self.assertEqual(self.git(local,'rev-parse','HEAD'),self.git(remote,'rev-parse','main'))
            self.assertEqual(len(list((Path(root)/'backups').glob('*.bundle'))), 2)

    def test_repeated_race_is_bounded_and_local_original_survives(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, other, archive, receipt = self.setup(root)
            hook=local/'.git/hooks/pre-push'
            hook.write_text('#!/bin/sh\nset -e\ngit -C '+shlex.quote(str(other))+' commit --allow-empty -m race\n'
                            'git -C '+shlex.quote(str(other))+' push origin main\n')
            hook.chmod(0o700)
            with self.assertRaisesRegex(RuntimeError,'retry limit'):
                module.synchronize(local, Path(root)/'backups', True, str(remote), attempts=2)
            self.assertTrue((local/archive).exists())
            self.assertTrue((local/receipt).exists())
            self.assertEqual(self.git(local,'status','--porcelain'), '')

    def test_conflicting_receipt_or_history_aborts_without_rewriting_head(self):
        for kind in ('receipt', 'history', 'private'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                local, remote, other, archive, receipt = self.setup(root)
                if kind=='receipt':
                    target=other/receipt;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('{"different":true}')
                elif kind=='history':
                    (other/module.HISTORY).write_text('{"updated_at":"a","rewritten":true}\n')
                else:
                    (local/'private.log').write_text('never publish')
                    self.git(local,'add','.');self.git(local,'commit','-m','unknown local output')
                self.git(other,'add','.');self.git(other,'commit','--allow-empty','-m','conflict');self.git(other,'push')
                before=self.git(local,'rev-parse','HEAD')
                with self.assertRaises(RuntimeError):
                    module.synchronize(local, Path(root)/'backups', True, str(remote))
                self.assertEqual(self.git(local,'rev-parse','HEAD'),before)
                self.assertEqual(self.git(local,'status','--porcelain'), '')

    def test_unknown_local_only_commit_cannot_be_pushed_even_without_divergence(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, other, archive, receipt = self.setup(root)
            module.synchronize(local, Path(root)/'backups', True, str(remote))
            before = self.git(remote, 'rev-parse', 'main')
            (local/'private.log').write_text('never publish')
            self.git(local,'add','.'); self.git(local,'commit','-m','unknown')
            with self.assertRaisesRegex(RuntimeError,'Unexpected local changes'):
                module.synchronize(local, Path(root)/'backups', True, str(remote))
            self.assertEqual(self.git(remote,'rev-parse','main'), before)
