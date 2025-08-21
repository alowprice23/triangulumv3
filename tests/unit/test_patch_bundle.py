import unittest
from pathlib import Path
import os
import shutil

from tooling.patch_bundle import create_patch_bundle, apply_patch_bundle

class TestPatchBundle(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_patch_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.file_path = "test_file.txt"
        self.full_path = self.test_dir / self.file_path

    def test_create_and_apply_patch_bundle(self):
        original_content = "Hello, world!\nThis is the original file.\n"
        modified_content = "Hello, Python!\nThis is the modified file.\n"

        self.full_path.write_text(original_content)

        # 1. Create patch
        bundle = create_patch_bundle(
            original_files={self.file_path: original_content},
            modified_files={self.file_path: modified_content}
        )

        self.assertIn(self.file_path, bundle)
        self.assertIn("--- a/test_file.txt", bundle[self.file_path])
        self.assertIn("+++ b/test_file.txt", bundle[self.file_path])
        self.assertIn("-Hello, world!", bundle[self.file_path])
        self.assertIn("+Hello, Python!", bundle[self.file_path])

        # 2. Apply patch
        # The apply function works relative to a repo_root
        results = apply_patch_bundle(bundle, self.test_dir)

        self.assertEqual(results["applied"], [self.file_path])
        self.assertEqual(len(results["failed"]), 0)

        # 3. Verify content
        content_after_patch = self.full_path.read_text()
        self.assertEqual(content_after_patch, modified_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
