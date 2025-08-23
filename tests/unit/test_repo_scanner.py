import unittest
from pathlib import Path
import tempfile
import shutil

from discovery.ignore_rules import IgnoreRules
from discovery.repo_scanner import RepoScanner

class TestRepoScanner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "project"
        self.project_root.mkdir()
        (self.project_root / "file1.txt").write_text("hello")
        (self.project_root / "file2.log").write_text("log")
        sub = self.project_root / "subdir"
        sub.mkdir()
        (sub / "file3.py").write_text("print('hello')")
        (self.project_root / ".gitignore").write_text("*.log\n.git/")

        # Create a dummy .git directory to test ignoring it
        (self.project_root / ".git").mkdir()
        (self.project_root / ".git" / "config").write_text("test")


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_with_ignored_files(self):
        """Tests scanning a repository with some files and ignored files."""
        # Create ignore rules from a .gitignore file (if one were present)
        # For this test, we'll manually create the rules
        ignore_rules = IgnoreRules(additional_patterns=["*.log", ".git/"])
        scanner = RepoScanner(ignore_rules)
        manifest = scanner.scan(self.project_root)

        paths = {item["path"] for item in manifest}

        self.assertIn("file1.txt", paths)
        self.assertIn(str(Path("subdir") / "file3.py"), paths)
        self.assertIn(".gitignore", paths)
        self.assertNotIn("file2.log", paths)
        self.assertNotIn(str(Path(".git") / "config"), paths)
        self.assertEqual(len(manifest), 3) # file1.txt, subdir/file3.py, .gitignore

    def test_scan_empty_repo(self):
        """Tests scanning an empty repository."""
        empty_dir = self.project_root / "empty"
        empty_dir.mkdir()
        scanner = RepoScanner(IgnoreRules())
        manifest = scanner.scan(empty_dir)
        self.assertEqual(len(manifest), 0)

    def test_scan_non_existent_repo(self):
        """Tests scanning a non-existent repository."""
        scanner = RepoScanner(IgnoreRules())
        with self.assertRaises(ValueError):
            scanner.scan(Path("/non/existent/path"))

if __name__ == '__main__':
    unittest.main()
