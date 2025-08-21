import unittest
import networkx as nx
from pathlib import Path
import os
import shutil

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph

class TestDepGraph(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("test_project_dg")
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
        self.symbol_index = build_symbol_index(self.repo_root, self.all_files)

    def test_build_dependency_graph(self):
        graph = build_dependency_graph(self.symbol_index, self.all_files)

        main_py = os.path.join("main.py")
        utils_py = os.path.join("utils.py")
        user_py = os.path.join("models", "user.py")
        base_py = os.path.join("models", "base.py")

        self.assertTrue(graph.has_edge(main_py, utils_py))
        self.assertTrue(graph.has_edge(main_py, user_py))
        self.assertTrue(graph.has_edge(user_py, base_py))

    def tearDown(self):
        shutil.rmtree(self.repo_root)

if __name__ == '__main__':
    unittest.main()
