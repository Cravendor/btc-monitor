import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('recover_snapshot', Path(__file__).parents[1] / 'nas/recover_pending_snapshot.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryTests(unittest.TestCase):
    def add_receipt(self, local, path=None, content='{"original_receipt":true}\n'):
        path = path or 'data/task-executions/nas/watchdog/20261026T004002Z.json'
        target = local / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        self.git(local, 'add', '--', path)
        self.git(local, 'commit', '--amend', '--no-edit')
        return path, self.git(local, 'rev-parse', 'HEAD')

    def test_recovery_preserves_seven_receipts_and_identical_remote_copy(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, head, archive = self.setup_repo(root)
            originals = {}
            for minute in ('0040', '0045', '0050', '0055', '0100', '0105', '0110'):
                path, head = self.add_receipt(local,
                    'data/task-executions/nas/watchdog/20261026T' + minute + '02Z.json')
                originals[path] = (local / path).read_bytes()
            other = Path(root) / 'github'
            same = other / path
            same.parent.mkdir(parents=True, exist_ok=True)
            same.write_bytes(originals[path])
            self.git(other, 'add', '.'); self.git(other, 'commit', '-m', 'same receipt'); self.git(other, 'push')
            module.recover(local, head, archive, Path(root) / 'backup.bundle', str(remote))
            for path, raw in originals.items():
                self.assertEqual((local / path).read_bytes(), raw)
                self.assertEqual(self.git(local, 'rev-parse', 'HEAD:' + path),
                                 self.git(remote, 'rev-parse', 'main:' + path))

    def test_conflicting_receipt_aborts_and_preserves_pending_commit(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, head, archive = self.setup_repo(root)
            path, head = self.add_receipt(local)
            other = Path(root) / 'github'
            target = other / path; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('{"different":true}\n')
            self.git(other, 'add', '.'); self.git(other, 'commit', '-m', 'different receipt'); self.git(other, 'push')
            with self.assertRaisesRegex(RuntimeError, 'Unexpected merge conflict'):
                module.recover(local, head, archive, Path(root) / 'backup.bundle', str(remote))
            self.assertEqual(self.git(local, 'rev-parse', 'HEAD'), head)
            self.assertEqual(self.git(local, 'status', '--porcelain'), '')
            self.assertTrue((Path(root) / 'backup.bundle').exists())
            self.assertEqual(json.loads((local / path).read_text()), {'original_receipt': True})

    def test_modified_deleted_or_symlink_receipt_is_rejected(self):
        for kind in ('modified', 'deleted', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                local, remote, head, archive = self.setup_repo(root)
                path = 'data/task-executions/nas/storage/20261026T004002Z.json'
                target = local / path; target.parent.mkdir(parents=True, exist_ok=True)
                if kind == 'symlink':
                    target.symlink_to('../../../latest.json')
                else:
                    # Put an existing receipt in the parent without changing the
                    # pending snapshot's five required paths.
                    parent = self.git(local, 'rev-parse', 'HEAD^')
                    self.git(local, 'checkout', '-b', 'receipt-base', parent)
                    target.write_text('{"old":true}\n')
                    self.git(local, 'add', '.'); self.git(local, 'commit', '-m', 'old receipt')
                    base = self.git(local, 'rev-parse', 'HEAD')
                    self.git(local, 'checkout', 'main')
                    self.git(local, 'rebase', '--onto', base, parent)
                    if kind == 'deleted':
                        target.unlink()
                    else:
                        target.write_text('{"changed":true}\n')
                self.git(local, 'add', '.'); self.git(local, 'commit', '--amend', '--no-edit')
                head = self.git(local, 'rev-parse', 'HEAD')
                backup = Path(root) / 'backup.bundle'
                with self.assertRaisesRegex(RuntimeError, 'newly added regular files'):
                    module.recover(local, head, archive, backup, str(remote))
                self.assertFalse(backup.exists())
                self.assertEqual(self.git(local, 'rev-parse', 'HEAD'), head)

    def test_unexpected_extra_file_is_rejected_before_backup(self):
        with tempfile.TemporaryDirectory() as root:
            local, remote, head, archive = self.setup_repo(root)
            path, head = self.add_receipt(local, 'data/task-executions/nas/watchdog/private-log.json')
            backup = Path(root) / 'backup.bundle'
            with self.assertRaisesRegex(RuntimeError, 'Unexpected local files'):
                module.recover(local, head, archive, backup, str(remote))
            self.assertFalse(backup.exists())

    def git(self, folder, *args):
        return subprocess.check_output(['git', '-C', str(folder), *args], stderr=subprocess.DEVNULL, text=True).strip()

    def setup_repo(self, root, conflict=False):
        root = Path(root); remote=root/'remote.git'; local=root/'nas'; other=root/'github'
        subprocess.run(['git', 'init', '--bare', str(remote)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'clone', str(remote), str(local)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.git(local, 'checkout', '-b', 'main')
        self.git(local, 'config', 'user.name', 'test');self.git(local, 'config', 'user.email', 'test@example.com')
        for path in module.VIEWS + [module.HISTORY]:
            p=local/path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps({'updated_at':'a'})+'\n')
        self.git(local, 'add', '.');self.git(local, 'commit', '-m', 'base');self.git(local, 'push', '-u', 'origin', 'main')
        subprocess.run(['git','clone','-b','main',str(remote),str(other)], check=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.git(other,'config','user.name','test');self.git(other,'config','user.email','test@example.com')
        archive='data/2026/10/25/original.json';(local/archive).parent.mkdir(parents=True);(local/archive).write_text('{"original":true}\n')
        for path in module.VIEWS:(local/path).write_text('{"source":"nas"}\n')
        (local/module.HISTORY).write_text('{"updated_at":"a"}\n{"updated_at":"local"}\n')
        self.git(local,'add','.');self.git(local,'commit','-m','pending');head=self.git(local,'rev-parse','HEAD')
        for path in module.VIEWS:(other/path).write_text('{"source":"remote"}\n')
        (other/module.HISTORY).write_text('{"updated_at":"a"}\n'+json.dumps({'updated_at':'local' if conflict else 'remote','value':1})+'\n')
        (other/'new-code.py').write_text('# preserve remote code\n')
        self.git(other,'add','.');self.git(other,'commit','-m','remote');self.git(other,'push')
        return local, remote, head, archive

    def test_recovery_preserves_snapshot_histories_and_new_remote_code(self):
        with tempfile.TemporaryDirectory() as root:
            local,remote,head,archive=self.setup_repo(root)
            backup=Path(root)/'backup.bundle'
            original=(local/archive).read_bytes()
            module.recover(local,head,archive,backup,str(remote))
            self.assertTrue(backup.exists())
            self.assertEqual((local/archive).read_bytes(), original)
            self.assertTrue((local/'new-code.py').exists())
            rows=[json.loads(x)['updated_at'] for x in (local/module.HISTORY).read_text().splitlines()]
            self.assertEqual(set(rows),{'a','local','remote'})
            self.assertEqual(self.git(local,'status','--porcelain'),'')
            self.assertEqual(self.git(local,'rev-parse','HEAD'),self.git(remote,'rev-parse','main'))
            self.assertEqual(json.loads((local/module.VIEWS[0]).read_text())['source'],'remote')

    def test_conflicting_original_timestamp_stops_without_rewriting_local_commit(self):
        with tempfile.TemporaryDirectory() as root:
            local,remote,head,archive=self.setup_repo(root,conflict=True)
            backup=Path(root)/'backup.bundle'
            with self.assertRaisesRegex(RuntimeError,'Conflicting original history'):
                module.recover(local,head,archive,backup,str(remote))
            self.assertTrue(backup.exists())
            self.assertEqual(self.git(local,'rev-parse','HEAD'),head)
            self.assertEqual(self.git(local,'status','--porcelain'),'')

    def test_changed_head_dirty_tree_and_existing_backup_refuse_repair(self):
        with tempfile.TemporaryDirectory() as root:
            local,remote,head,archive=self.setup_repo(root)
            backup=Path(root)/'backup.bundle'
            with self.assertRaisesRegex(RuntimeError,'HEAD changed'):
                module.recover(local,'0'*40,archive,backup,str(remote))
            (local/'private-log.txt').write_text('keep')
            with self.assertRaisesRegex(RuntimeError,'Uncommitted'):
                module.recover(local,head,archive,backup,str(remote))
            self.assertFalse(backup.exists())
            backup.write_text('keep backup')
            with self.assertRaises(ValueError):module.recover(local,head,archive,backup,str(remote))
            self.assertEqual(backup.read_text(),'keep backup')

    def test_unexpected_archive_conflict_aborts_merge_and_keeps_original(self):
        with tempfile.TemporaryDirectory() as root:
            local,remote,head,archive=self.setup_repo(root)
            other=Path(root)/'github'
            (other/archive).parent.mkdir(parents=True,exist_ok=True)
            (other/archive).write_text('{"different":true}\n')
            self.git(other,'add','.');self.git(other,'commit','-m','conflicting archive');self.git(other,'push')
            with self.assertRaisesRegex(RuntimeError,'Unexpected merge conflict'):
                module.recover(local,head,archive,Path(root)/'backup.bundle',str(remote))
            self.assertEqual(self.git(local,'rev-parse','HEAD'),head)
            self.assertEqual(self.git(local,'status','--porcelain'),'')
            self.assertEqual(json.loads((local/archive).read_text()),{'original':True})

    def test_rejected_push_keeps_both_merge_and_backup_for_review(self):
        with tempfile.TemporaryDirectory() as root:
            local,remote,head,archive=self.setup_repo(root)
            hook=local/'.git/hooks/pre-push';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o700)
            backup=Path(root)/'backup.bundle'
            with self.assertRaisesRegex(RuntimeError,'Git push failed'):
                module.recover(local,head,archive,backup,str(remote))
            self.assertTrue(backup.exists())
            self.assertNotEqual(self.git(local,'rev-parse','HEAD'),head)
            self.assertEqual(self.git(local,'status','--porcelain'),'')
            self.assertEqual(json.loads((local/archive).read_text()),{'original':True})
