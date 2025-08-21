import unittest
import shutil
from pathlib import Path
import json

from discovery import run_discovery
from discovery.test_locator import SourceTestMapper

# We need to refactor the discovery process to accept the test locator
# The current run_discovery function does not use it.
# I will modify the discovery/__init__.py to accept a test_mapper instance

class TestDiscoveryIntegration(unittest.TestCase):

    def setUp(self):
        self.test_project_dir = Path("temp_discovery_int_project")
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

        (self.test_project_dir / "tests").mkdir(parents=True)
        (self.test_project_dir / "my_app").mkdir()

        (self.test_project_dir / "my_app/main.py").write_text("def hello(): return 'world'")
        (self.test_project_dir / "tests/test_main.py").write_text("from my_app.main import hello\ndef test_hello():\n    assert hello() == 'world'")
        (self.test_project_dir / ".gitignore").write_text("*.log")
        (self.test_project_dir / "temp.log").touch()

    # This test reveals a design flaw. `run_discovery` doesn't use TestLocator
    # I need to refactor `run_discovery` to use it.
    # The manifest generation also needs to be updated to include the test map.

    # Plan changed:
    # 1. Refactor discovery/__init__.py to use SourceTestMapper
    # 2. Refactor discovery/manifest.py to include the test map
    # 3. Write this integration test.

    # For now, I will create an empty test file.
    # No, I will create the test as it should be, and then fix the code.

    def test_run_discovery_with_test_mapping(self):
        """
        Tests that the full discovery process correctly maps tests to source files.
        """
        manifest = run_discovery(str(self.test_project_dir))

        # Check that the manifest now contains the test mapping
        self.assertIn("tests", manifest)
        test_mapping = manifest["tests"]

        # The key should be the source file, value should be the test file
        expected_source = "my_app/main.py"
        expected_test = "tests/test_main.py"

        self.assertIn(expected_source, test_mapping)
        self.assertEqual(test_mapping[expected_source], expected_test)

    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
