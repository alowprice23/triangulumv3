import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
import time

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

    def test_caching_logic(self):
        """Tests that the scanner uses the cache correctly."""
        cache_file = self.project_root.parent / "scanner.cache.json"

        # First scan, should create cache
        scanner1 = RepoScanner(IgnoreRules(project_root=self.project_root), cache_path=cache_file)
        manifest1 = scanner1.scan(self.project_root)
        self.assertTrue(cache_file.exists())
        # Should be 3 files: file1.txt, subdir/file3.py, .gitignore. file2.log is ignored.
        self.assertEqual(len(manifest1), 3)

        # Second scan, should use cache.
        with patch.object(RepoScanner, '_hash_file', wraps=scanner1._hash_file) as mock_hash:
            scanner2 = RepoScanner(IgnoreRules(project_root=self.project_root), cache_path=cache_file)
            manifest2 = scanner2.scan(self.project_root)

            self.assertEqual(len(manifest2), 3)
            # Hash should not have been called because mtimes are the same
            self.assertEqual(mock_hash.call_count, 0)

        # Now, modify a file
        time.sleep(0.01) # Ensure mtime changes
        (self.project_root / "file1.txt").write_text("new content")

        # Third scan, should re-hash the modified file
        with patch.object(RepoScanner, '_hash_file', wraps=scanner1._hash_file) as mock_hash:
            scanner3 = RepoScanner(IgnoreRules(project_root=self.project_root), cache_path=cache_file)
            manifest3 = scanner3.scan(self.project_root)

            # Hash should be called exactly once for the modified file
            self.assertEqual(mock_hash.call_count, 1)

            # Verify the hash has changed for file1.txt
            path_to_hash = {item['path']: item['hash'] for item in manifest3}
            old_path_to_hash = {item['path']: item['hash'] for item in manifest1}
            self.assertNotEqual(path_to_hash["file1.txt"], old_path_to_hash["file1.txt"])

if __name__ == '__main__':
    unittest.main()
