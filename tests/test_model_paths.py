import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import model_paths
spec = importlib.util.spec_from_file_location('adopt', Path(model_paths.__file__).with_name('adopt-hf-cache.py'))
adopt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adopt)

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'HOME':str(self.home)}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.lock = {k:dict(repo_id='org/'+k,revision='a'*40) for k in model_paths.COMPONENTS}

    def test_cache_precedence_and_mia_reuse(self):
        os.environ['HF_HOME'] = str(self.home/'custom')
        self.assertEqual(model_paths.hub_cache(), self.home/'custom/hub')
        mia = model_paths.snapshot('draft', self.lock, self.home/'.cache/huggingface/hub')
        mia.mkdir(parents=True)
        self.assertEqual(model_paths.resolve('draft', self.lock), mia)
        os.environ['HF_HUB_CACHE'] = str(self.home/'hub-override')
        self.assertEqual(model_paths.hub_cache(), self.home/'hub-override')
        self.assertEqual(model_paths.resolve('carrier', self.lock), model_paths.snapshot('carrier', self.lock))
        self.assertEqual(model_paths.resolve('draft', self.lock, str(self.home/'explicit')), self.home/'explicit/draft')

    def test_adoption_reuses_bytes_and_preserves_docker_links(self):
        source = self.home/'models/draft'
        source.mkdir(parents=True)
        (source/'config.json').write_text('{"test": true}')
        inode = (source/'config.json').stat().st_ino
        destination = adopt.adopt('draft', source, self.lock)
        self.assertTrue(source.is_symlink())
        self.assertEqual((source/'config.json').read_text(), '{"test": true}')
        self.assertEqual((destination/'config.json').stat().st_ino, inode)
        self.assertTrue((destination/'config.json').is_symlink())
        mount, container = model_paths.mount(source, 'draft')
        self.assertEqual(Path(mount), destination.parent.parent)
        self.assertEqual(container, '/models/draft/snapshots/'+'a'*40)
        self.assertEqual(adopt.adopt('draft', source, self.lock), destination)

    def test_reuses_existing_lfs_asset_regardless_of_extension(self):
        source = self.home/'models/draft'
        source.mkdir(parents=True)
        (source/'figure.png').write_bytes(b'example LFS image')
        destination = model_paths.snapshot('draft', self.lock)
        destination.mkdir(parents=True)
        blob = destination.parent.parent/'blobs'/('b'*64)
        blob.parent.mkdir()
        blob.write_bytes(b'example LFS image')
        (destination/'figure.png').symlink_to('../../blobs/'+blob.name)
        adopt.adopt('draft', source, self.lock)
        self.assertEqual((source/'figure.png').read_bytes(), b'example LFS image')
        self.assertEqual((destination/'figure.png').resolve(), blob)

if __name__ == '__main__': unittest.main()
