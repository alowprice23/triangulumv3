import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil

from agents.coordinator import Coordinator

# Canned pytest JSON reports for mocking
FAILING_TEST_REPORT = {
    "summary": {"total": 2, "passed": 1, "failed": 1},
    "tests": [
        {
            "nodeid": "tests/test_math_ops.py::test_add_positive_numbers",
            "outcome": "failed",
            "longrepr": "assert 5 == 4"
        },
        {
            "nodeid": "tests/test_math_ops.py::test_add_negative_numbers",
            "outcome": "passed"
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
        },
        {
            "nodeid": "tests/test_math_ops.py::test_add_negative_numbers",
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
        shutil.copytree(self.repo_root, self.test_project_dir)

    @patch("agents.verifier.run_tests")
    @patch("agents.observer.run_tests")
    def test_full_debugging_cycle_success(self, mock_observer_run_tests, mock_verifier_run_tests):
        """
        Tests the full O->A->V cycle by mocking the test runner.
        This isolates the agent logic from the complexities of subprocess execution.
        """
        mock_observer_run_tests.return_value = FAILING_TEST_REPORT

        mock_verifier_run_tests.side_effect = [
            FAILING_TEST_REPORT,
            PASSING_TEST_REPORT,
            PASSING_TEST_REPORT
        ]

        coordinator = Coordinator(repo_root=self.test_project_dir)
        result = coordinator.run_debugging_cycle(
            bug_description="The add function is returning the wrong sum."
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("patch_bundle", result)

        patch_bundle = result["patch_bundle"]
        self.assertIn("math_ops.py", patch_bundle)
        patch_content = patch_bundle["math_ops.py"]

        # Corrected assertions
        self.assertIn("-    return a + b + 1", patch_content)
        self.assertIn("+    return a + b", patch_content)
        # Check that the context line is NOT prefixed with '+'
        self.assertIn(" def add(a, b):", patch_content)


    def tearDown(self):
        shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
