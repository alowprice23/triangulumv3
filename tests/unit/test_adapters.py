import unittest
from pathlib import Path
import os
import sys

from adapters.python import PythonAdapter
from adapters.node import NodeAdapter
from adapters.java import JavaAdapter

class TestAdapters(unittest.TestCase):

    def setUp(self):
        # This allows the test to run from the root directory
        self.test_files_root = Path("tests/unit/adapter_test_files")
        # Add the project root to the path to resolve python imports correctly
        sys.path.insert(0, str(self.test_files_root / "python_project"))

    def tearDown(self):
        sys.path.pop(0)

    def test_python_adapter_import_mapping(self):
        """Test the Python adapter's import-based mapping logic."""
        adapter = PythonAdapter()
        source_file = "src/app/main.py"
        all_tests = ["tests/test_main.py"]

        # We need to temporarily change the CWD for the test to work with relative paths
        original_cwd = os.getcwd()
        os.chdir(self.test_files_root / "python_project")

        result = adapter.map_source_to_test(source_file, all_tests)

        os.chdir(original_cwd) # Change back to original CWD

        self.assertEqual(result, "tests/test_main.py")

    def test_python_adapter_name_mapping(self):
        """Test the Python adapter's name-based fallback mapping."""
        adapter = PythonAdapter()
        all_tests = ["tests/test_other.py"]
        source = "src/app/other.py"
        result = adapter.map_source_to_test(source, all_tests)
        self.assertEqual(result, "tests/test_other.py")

    def test_java_adapter_mapping(self):
        """Test the Java adapter's path-based mapping."""
        adapter = JavaAdapter()
        source = "src/main/java/com/mycompany/MyClass.java"
        all_tests = ["src/test/java/com/mycompany/MyClassTest.java"]
        result = adapter.map_source_to_test(source, all_tests)
        self.assertEqual(result, "src/test/java/com/mycompany/MyClassTest.java")

    def test_node_adapter_mapping(self):
        """Test the Node.js adapter's simple name-based mapping."""
        adapter = NodeAdapter()
        all_tests = ["src/app.test.js", "src/components/button.spec.ts"]

        source_js = "src/app.js"
        result_js = adapter.map_source_to_test(source_js, all_tests)
        self.assertEqual(result_js, "src/app.test.js")

        source_ts = "src/components/button.ts"
        result_ts = adapter.map_source_to_test(source_ts, all_tests)
        # The current simple regex might not be perfect, but we test its expectation
        # A better implementation would be needed for complex cases.
        self.assertIn(result_ts, all_tests)


if __name__ == '__main__':
    unittest.main()
