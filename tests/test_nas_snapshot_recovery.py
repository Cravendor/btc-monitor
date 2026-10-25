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
