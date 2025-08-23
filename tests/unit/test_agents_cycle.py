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
    @patch("agents.coordinator.calculate_n_star")
    @patch("agents.coordinator.estimate_initial_entropy")
    @patch("agents.coordinator.build_dependency_graph")
    @patch("agents.coordinator.build_symbol_index")
    @patch("agents.coordinator.RepoScanner")
    @patch("agents.coordinator.Verifier")
    @patch("agents.coordinator.Analyst")
    @patch("agents.coordinator.Observer")
    @patch("agents.coordinator.MetaTuner")
    def test_full_debugging_cycle_success(self, mock_meta_tuner_class, mock_observer_class, mock_analyst_class, mock_verifier_class, mock_repo_scanner_class, mock_build_symbol_index, mock_build_dep_graph, mock_estimate_h0, mock_calculate_n_star):
        """
        Tests the full O->A->V cycle, mocking agents and entropy calculations.
        """
        # Mock the discovery and entropy components
        mock_repo_scanner_instance = mock_repo_scanner_class.return_value
        mock_repo_scanner_instance.scan.return_value = [{"path": "math_ops.py"}]
        mock_build_symbol_index.return_value = {}
        mock_build_dep_graph.return_value = MagicMock() # Return a mock graph
        mock_estimate_h0.return_value = 10.0
        mock_calculate_n_star.return_value = 5 # Let's say N* is 5

        mock_observer_instance = mock_observer_class.return_value
        mock_analyst_instance = mock_analyst_class.return_value
        mock_verifier_instance = mock_verifier_class.return_value

        mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["tests/test_math_ops.py::test_add"]}

        mock_analyst_instance.analyze_and_propose_patch.return_value = {
            "status": "success",
            "patch_bundle": {"math_ops.py": "dummy_patch"},
            "files_changed": ["math_ops.py"],
            "original_error_log": "assert 5 == 4",
            "g_estimation": 2.0 # Analyst estimates g=2.0
        }

        mock_verifier_instance.verify_changes.side_effect = [
            {"status": "fail"},
            {"status": "success"}
        ]

        coordinator = Coordinator(repo_root=self.test_project_dir)
        result = coordinator.run_debugging_cycle(
            bug_description="The add function is returning the wrong sum."
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("patch_bundle", result)

        # Verify that the dynamic budget was calculated
        mock_estimate_h0.assert_called_once()
        # Check that N* was calculated twice: once with g=1.0, and once with g=2.0
        self.assertEqual(mock_calculate_n_star.call_count, 2)
        mock_calculate_n_star.assert_called_with(10.0, 2.0)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("agents.coordinator.request_human_feedback")
    @patch("agents.coordinator.calculate_n_star")
    @patch("agents.coordinator.estimate_initial_entropy")
    @patch("agents.coordinator.build_dependency_graph")
    @patch("agents.coordinator.build_symbol_index")
    @patch("agents.coordinator.RepoScanner")
    @patch("agents.coordinator.Verifier")
    @patch("agents.coordinator.Analyst")
    @patch("agents.coordinator.Observer")
    @patch("agents.coordinator.MetaTuner")
    def test_failure_hint_is_accumulated(self, mock_meta_tuner_class, mock_observer_class, mock_analyst_class, mock_verifier_class, mock_repo_scanner_class, mock_build_symbol_index, mock_build_dep_graph, mock_estimate_h0, mock_calculate_n_star, mock_human_feedback):
        """
        Tests that hints from failed attempts are passed to the Analyst.
        """
        # Mock discovery and entropy
        mock_repo_scanner_instance = mock_repo_scanner_class.return_value
        mock_repo_scanner_instance.scan.return_value = [{"path": "math_ops.py"}]
        mock_estimate_h0.return_value = 10.0
        mock_calculate_n_star.return_value = 3 # N* is 3

        # Mock agents
        mock_observer_instance = mock_observer_class.return_value
        mock_analyst_instance = mock_analyst_class.return_value
        mock_tuner_instance = mock_meta_tuner_class.return_value

        mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test"], "logs": "original log"}

        # First call to analyst fails
        mock_analyst_instance.analyze_and_propose_patch.return_value = {"status": "failed", "reason": "Reason 1"}

        # Mock tuner to return a hint
        hint = "Hint from failed attempt."
        mock_tuner_instance.tune_from_outcome.return_value = hint

        # Mock human feedback to avoid stdin read error on final escalation
        mock_human_feedback.return_value = "Final hint"

        coordinator = Coordinator(repo_root=self.test_project_dir)
        # We don't care about the final result, just the interactions
        coordinator.run_debugging_cycle("a bug")

        # Verify tuner was called
        mock_tuner_instance.tune_from_outcome.assert_called()

        # Verify analyst was called multiple times
        self.assertGreater(mock_analyst_instance.analyze_and_propose_patch.call_count, 1)

        # Verify the hint was passed to the second call
        second_call_args = mock_analyst_instance.analyze_and_propose_patch.call_args_list[1]
        observer_report_for_second_call = second_call_args[0][0]
        self.assertIn(hint, observer_report_for_second_call["logs"])


    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

if __name__ == '__main__':
    unittest.main()
