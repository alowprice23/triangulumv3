import unittest
import json
from pathlib import Path
import os
import shutil

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from discovery.scope_proposals import propose_scopes
from discovery.manifest import generate_manifest, save_manifest

class TestManifest(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("test_project_m")
        self.repo_root.mkdir(exist_ok=True)
        (self.repo_root / "models").mkdir(exist_ok=True)

        (self.repo_root / "main.py").write_text("import utils\nfrom models import user")
        (self.repo_root / "utils.py").write_text("# utils")
        (self.repo_root / "models/__init__.py").touch()
        (self.repo_root / "models/user.py").write_text("from . import base")
        (self.repo_root / "models/base.py").write_text("# base")

        self.all_files = [
            os.path.join("main.py"),
            os.path.join("utils.py"),
            os.path.join("models", "__init__.py"),
            os.path.join("models", "user.py"),
            os.path.join("models", "base.py")
        ]
        symbol_index = build_symbol_index(self.repo_root, self.all_files)
        self.graph = build_dependency_graph(symbol_index, self.all_files)
        self.proposals = propose_scopes(self.graph, self.all_files, "models/user.py", self.repo_root)

    def test_generate_manifest(self):
        manifest = generate_manifest(self.repo_root, self.all_files, self.graph, self.proposals)
        self.assertIn("version", manifest)
        self.assertEqual(len(manifest["files"]), len(self.all_files))
        self.assertTrue(all("hash" in f for f in manifest["files"]))

    def test_save_manifest(self):
        manifest = generate_manifest(self.repo_root, self.all_files, self.graph, self.proposals)
        output_path = self.repo_root / "test_manifest.json"
        save_manifest(manifest, output_path)
        self.assertTrue(output_path.exists())

    def tearDown(self):
        shutil.rmtree(self.repo_root)

if __name__ == '__main__':
    unittest.main()
