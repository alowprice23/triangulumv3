import unittest
import networkx as nx
from pathlib import Path
import os
import shutil

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from discovery.family_tree import get_family_tree

class TestFamilyTree(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("test_project_ft")
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

    def test_get_family_tree(self):
        target_file = os.path.join("models", "user.py")
        family_tree = get_family_tree(self.graph, target_file)

        expected_family = {
            os.path.join("models", "user.py"),
            os.path.join("models", "base.py"),
            os.path.join("main.py")
        }

        self.assertEqual(family_tree, expected_family)

    def tearDown(self):
        shutil.rmtree(self.repo_root)

if __name__ == '__main__':
    unittest.main()
