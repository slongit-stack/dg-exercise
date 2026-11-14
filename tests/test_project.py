"""Replay packaging guardrails; no real data mutation or inference."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts import project


class ProjectTests(unittest.TestCase):
    def test_restore_checks_all_conflicts_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            conflict=root/'existing'
            conflict.write_bytes(b'original')
            new=root/'new'
            with self.assertRaises(ValueError):
                project.restore([(new,b'new'),(conflict,b'changed')])
            self.assertFalse(new.exists())
            self.assertEqual(conflict.read_bytes(),b'original')

    def test_restore_is_idempotent_for_equal_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'nested/input'
            project.restore([(path,b'input')])
            project.restore([(path,b'input')])
            self.assertEqual(path.read_bytes(),b'input')

    def test_archive_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/'artifacts'
            folder.mkdir()
            archive=folder/'bad.tar.gz'
            with tarfile.open(archive,'w:gz') as tar:
                member=tarfile.TarInfo('../escape')
                member.size=1
                tar.addfile(member,io.BytesIO(b'x'))
            manifest=dict(archive=archive.name,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                          files=[dict(path='../escape',bytes=1,sha256=hashlib.sha256(b'x').hexdigest())])
            (folder/'pilot_replay_manifest.json').write_text(json.dumps(manifest))
            with patch.object(project,'ROOT',root):
                with self.assertRaises(ValueError):
                    project.bundle_entries()


if __name__=='__main__':
    unittest.main()
