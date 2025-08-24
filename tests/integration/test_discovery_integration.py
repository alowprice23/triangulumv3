import unittest
import shutil
from pathlib import Path
import json

from discovery.code_graph import CodeGraphBuilder
from adapters.python import PythonAdapter

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

    def test_run_discovery_with_test_mapping(self):
        """
        Tests that the full discovery process correctly builds a code graph.
        """
        adapter = PythonAdapter()
        builder = CodeGraphBuilder(repo_root=self.test_project_dir, adapter=adapter)
        code_graph = builder.build()

        # Check that the code graph is not empty
        self.assertIsNotNone(code_graph)
        self.assertIsInstance(code_graph.metadata, dict)
        self.assertGreater(len(code_graph.manifest), 0)
        self.assertGreater(len(code_graph.symbol_index), 0)
        self.assertGreater(len(code_graph.dependency_graph.nodes), 0)

        # TODO: Add assertions for test mapping once the schema is clear.

    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
