import unittest
from pathlib import Path
import os
import shutil

from tooling.test_runner import run_tests

class TestTestRunner(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path(os.getcwd())
        # Create the necessary test project for the test_family_tree.py to run against
        self.test_project_dir = self.repo_root / "test_project_ft"
        self.test_project_dir.mkdir(exist_ok=True)
        (self.test_project_dir / "models").mkdir(exist_ok=True)
        (self.test_project_dir / "main.py").write_text("from models import user")
        (self.test_project_dir / "models/user.py").write_text("from . import base")
        (self.test_project_dir / "models/base.py").touch()
        (self.test_project_dir / "models/__init__.py").touch()
        (self.test_project_dir / "utils.py").touch()


    def test_run_specific_tests(self):
        # This test needs the setup from test_symbol_index, etc.
        # It's better to test against a test that has its own setup.
        # Let's run a test from the original suite that has no deps, like test_crc
        result = run_tests(repo_root=self.repo_root, test_targets=["tests/unit/test_crc.py"])
        self.assertNotIn("error", result)
        self.assertGreater(result["summary"]["total"], 0)

    def test_run_with_pytest_args(self):
        # Use -k to select a test by name from test_family_tree
        # This test now creates its own project, so we can run it.
        result = run_tests(
            repo_root=self.repo_root,
            test_targets=["tests/unit/test_family_tree.py"],
            pytest_args=["-k", "test_get_family_tree"]
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["summary"]["total"], 1)
        self.assertEqual(result["summary"]["passed"], 1)

    def test_no_tests_found(self):
        result = run_tests(
            repo_root=self.repo_root,
            pytest_args=["-k", "non_existent_test_name_xyz"]
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["exit_code"], 5)
        self.assertEqual(result["summary"]["total"], 0)

    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
