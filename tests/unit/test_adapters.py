import unittest
from unittest.mock import patch
from pathlib import Path

from adapters.python import PythonAdapter
from adapters.node import NodeAdapter
from discovery.test_locator import SourceTestMapper # Updated import

class TestAdapters(unittest.TestCase):

    def test_python_adapter_mapping(self):
        adapter = PythonAdapter()
        all_tests = ["tests/test_main.py", "tests/api/test_core.py"]

        source = "main.py"
        result = adapter.map_source_to_test(source, all_tests)
        self.assertEqual(result, "tests/test_main.py")

        source_nested = "api/core.py"
        result_nested = adapter.map_source_to_test(source_nested, all_tests)
        self.assertEqual(result_nested, "tests/api/test_core.py")

        source_no_match = "logic.py"
        result_no_match = adapter.map_source_to_test(source_no_match, all_tests)
        self.assertIsNone(result_no_match)

    def test_node_adapter_mapping(self):
        adapter = NodeAdapter()
        all_tests = ["src/app.test.js", "src/components/button.spec.ts"]

        source_js = "src/app.js"
        result_js = adapter.map_source_to_test(source_js, all_tests)
        self.assertEqual(result_js, "src/app.test.js")

        source_ts = "src/components/button.ts"
        result_ts = adapter.map_source_to_test(source_ts, all_tests)
        self.assertEqual(result_ts, "src/components/button.spec.ts")

    @patch('discovery.language_probe.probe_language')
    def test_source_test_mapper(self, mock_probe_language): # Renamed test method
        """Test that the mapper uses the correct adapter."""
        mock_probe_language.return_value = "Python"

        all_files = [
            "app/main.py",
            "app/utils.py",
            "tests/test_main.py"
        ]

        mapper = SourceTestMapper() # Use new class name
        mapping = mapper.locate_tests(all_files, repo_root=Path("."))

        self.assertIn("app/main.py", mapping)
        self.assertEqual(mapping["app/main.py"], "tests/test_main.py")
        self.assertNotIn("app/utils.py", mapping)


if __name__ == '__main__':
    unittest.main()
