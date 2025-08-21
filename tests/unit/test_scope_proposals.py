import unittest
import networkx as nx
from pathlib import Path
import os
import shutil

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from discovery.scope_proposals import propose_scopes

class TestScopeProposals(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("test_project_sp")
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

    def test_propose_scopes_for_file(self):
        target_file = os.path.join("models", "user.py")
        proposals = propose_scopes(self.graph, self.all_files, target_file, self.repo_root)
        self.assertEqual(len(proposals), 2)
        self.assertTrue(proposals[0]["name"].startswith("surgical_scope"))

    def test_propose_scopes_for_directory(self):
        target_dir = "models"
        proposals = propose_scopes(self.graph, self.all_files, target_dir, self.repo_root)
        self.assertEqual(len(proposals), 2)
        self.assertEqual(proposals[0]["name"], "component_scope_for_models")

    def tearDown(self):
        shutil.rmtree(self.repo_root)

if __name__ == '__main__':
    unittest.main()
