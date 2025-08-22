import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import os

from agents.coordinator import Coordinator

# Canned pytest JSON reports for mocking
FAILING_TEST_REPORT = {
    "summary": {"total": 2, "passed": 1, "failed": 1},
    "tests": [
        {
            "nodeid": "tests/test_math_ops.py::test_add_positive_numbers",
            "outcome": "failed",
            "longrepr": "assert 5 == 4"
        }
    ],
    "exit_code": 1
}

PASSING_TEST_REPORT = {
    "summary": {"total": 2, "passed": 2, "failed": 0},
    "tests": [
        {
            "nodeid": "tests/test_math_ops.py::test_add_positive_numbers",
            "outcome": "passed"
        }
    ],
    "exit_code": 0
}


class TestAgentsCycle(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path("buggy_project")
        self.test_project_dir = Path("temp_buggy_project")
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)
        if not self.repo_root.exists():
            self.repo_root.mkdir()
            (self.repo_root / "tests").mkdir(parents=True)
            (self.repo_root / "__init__.py").touch()
            (self.repo_root / "tests/__init__.py").touch()
            (self.repo_root / "math_ops.py").write_text("# Buggy file\ndef add(a, b):\n    return a + b + 1")
            (self.repo_root / "tests/test_math_ops.py").write_text("from math_ops import add\ndef test_add():\n    assert add(2, 2) == 4")

        shutil.copytree(self.repo_root, self.test_project_dir)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("agents.coordinator.Verifier")
    @patch("agents.coordinator.Analyst")
    @patch("agents.coordinator.Observer")
    @patch("agents.coordinator.MetaTuner")
    def test_full_debugging_cycle_success(self, mock_meta_tuner_class, mock_observer_class, mock_analyst_class, mock_verifier_class):
        """
        Tests the full O->A->V cycle by mocking the agent methods.
        """
        mock_observer_instance = mock_observer_class.return_value
        mock_analyst_instance = mock_analyst_class.return_value
        mock_verifier_instance = mock_verifier_class.return_value

        mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["tests/test_math_ops.py::test_add"]}

        mock_analyst_instance.analyze_and_propose_patch.return_value = {
            "status": "success",
            "patch_bundle": {"math_ops.py": "dummy_patch"},
            "files_changed": ["math_ops.py"],
            "original_error_log": "assert 5 == 4"
        }

        mock_verifier_instance.verify_changes.side_effect = [
            {"status": "fail"},
            {"status": "success"}
        ]

        coordinator = Coordinator(repo_root=self.test_project_dir)
        result = coordinator.run_debugging_cycle(
            bug_description="The add function is returning the wrong sum.",
            initial_scope=["math_ops.py", "tests/test_math_ops.py"]
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("patch_bundle", result)

    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
