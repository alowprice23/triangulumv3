import unittest
from pathlib import Path
import os
import shutil

from discovery.symbol_index import build_symbol_index

class TestSymbolIndex(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("test_project_si")
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

    def test_build_symbol_index(self):
        symbol_index = build_symbol_index(self.repo_root, self.all_files)

        main_py_path = os.path.join('main.py')
        user_py_path = os.path.join('models', 'user.py')

        self.assertIn(main_py_path, symbol_index)
        self.assertEqual(symbol_index[main_py_path]["imports"], ["models.user", "utils"])

        self.assertIn(user_py_path, symbol_index)
        self.assertEqual(symbol_index[user_py_path]["imports"], [".base"])

    def tearDown(self):
        shutil.rmtree(self.repo_root)

if __name__ == '__main__':
    unittest.main()
