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
            (self.repo_root / "tests/test_math_ops.py").write_text("from ..math_ops import add\ndef test_add():\n    assert add(2, 2) == 4")

        shutil.copytree(self.repo_root, self.test_project_dir)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("api.openai_client.OpenAIClient.get_completion")
    @patch("agents.verifier.run_tests")
    @patch("agents.observer.run_tests")
    def test_full_debugging_cycle_success(self, mock_observer_run_tests, mock_verifier_run_tests, mock_get_completion):
        """
        Tests the full O->A->V cycle by mocking the test runner and LLM call.
        """
        mock_observer_run_tests.return_value = FAILING_TEST_REPORT

        mock_verifier_run_tests.side_effect = [
            FAILING_TEST_REPORT,
            PASSING_TEST_REPORT,
            PASSING_TEST_REPORT
        ]

        fixed_content = "# Buggy file\ndef add(a, b):\n    return a + b"
        llm_response = f"```python\n{fixed_content}\n```"
        mock_get_completion.return_value = llm_response

        coordinator = Coordinator(repo_root=self.test_project_dir)
        result = coordinator.run_debugging_cycle(
            bug_description="The add function is returning the wrong sum."
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("patch_bundle", result)

        patch_bundle = result["patch_bundle"]
        self.assertIn("math_ops.py", patch_bundle)
        patch_content = patch_bundle["math_ops.py"]

        self.assertIn("-    return a + b + 1", patch_content)
        self.assertIn("+    return a + b", patch_content)

    def tearDown(self):
        shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
