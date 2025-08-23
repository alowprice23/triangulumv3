import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import shutil

from agents.analyst import Analyst
from agents.coordinator import Coordinator
from kb.patch_motif_library import PatchMotifLibrary

class TestAdvancedAgents(unittest.TestCase):

    def setUp(self):
        # Create a dummy project for the coordinator to operate on
        self.repo_root = Path("temp_test_repo")
        if self.repo_root.exists():
            shutil.rmtree(self.repo_root)
        self.repo_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.repo_root)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('api.llm_router.OpenAIClient')
    @patch('kb.patch_motif_library.PatchMotifLibrary.find_similar_motifs')
    def test_analyst_uses_kb(self, mock_find_motifs, mock_openai_client_class):
        """Test that the Analyst includes KB context in its prompt."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.get_completion.return_value = "```python\nfixed_code\n```"
        mock_openai_client_class.return_value = mock_llm_instance
        mock_find_motifs.return_value = [{"metadata": {"source_file": "old.py", "patch": "p"}}]

        analyst = Analyst()
        with patch("pathlib.Path.read_text", return_value="content"):
            analyst.analyze_and_propose_patch({"failing_tests": ["t.py"], "logs": "e"}, self.repo_root, [], {})

        self.assertTrue(mock_llm_instance.get_completion.called)
        self.assertIn("Knowledge Base", mock_llm_instance.get_completion.call_args[0][0])

    @patch('agents.coordinator.request_human_feedback')
    @patch('agents.coordinator.Observer')
    @patch('agents.coordinator.Analyst')
    @patch('agents.coordinator.PatchMotifLibrary')
    @patch('agents.coordinator.MetaTuner')
    def test_coordinator_uses_kb_and_tuner_on_success(self, mock_tuner_class, mock_kb_class, mock_analyst_class, mock_observer_class, mock_human_feedback):
        """Test that the Coordinator calls the KB and tuner on a successful run."""
        with patch('agents.coordinator.Verifier') as mock_verifier_class:
            mock_analyst_instance = mock_analyst_class.return_value
            mock_kb_instance = mock_kb_class.return_value
            mock_tuner_instance = mock_tuner_class.return_value
            mock_observer_instance = mock_observer_class.return_value
            mock_verifier_instance = mock_verifier_class.return_value
            mock_analyst_instance.llm_config.model_name = "test-model"

            mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test.py"]}
            mock_analyst_instance.analyze_and_propose_patch.return_value = {"status": "success", "patch_bundle": {"file.py": "patch"}, "original_error_log": "error"}
            mock_verifier_instance.verify_changes.side_effect = [{"status": "fail"}, {"status": "success"}]

            coordinator = Coordinator(repo_root=self.repo_root)
            coordinator.scanner = MagicMock()
            coordinator.scanner.scan.return_value = [{"path": "file.py"}]
            coordinator.run_debugging_cycle("a bug")

            mock_kb_instance.add_motif.assert_called_once()
            mock_tuner_instance.tune_from_outcome.assert_called_once()

    @patch('agents.coordinator.request_human_feedback')
    @patch('agents.coordinator.RepoScanner')
    @patch('agents.coordinator.Observer')
    @patch('agents.coordinator.Analyst')
    def test_verifier_rejects_malicious_patch(self, mock_analyst_class, mock_observer_class, mock_repo_scanner_class, mock_human_feedback):
        """Test that a malicious patch from the Analyst is caught and rejected."""
        mock_repo_scanner_instance = mock_repo_scanner_class.return_value
        mock_repo_scanner_instance.scan.return_value = [{"path": "file.py"}]
        mock_observer_instance = mock_observer_class.return_value
        mock_analyst_instance = mock_analyst_class.return_value
        mock_analyst_instance.llm_config.model_name = "test-model"

        # The analyst proposes a patch containing a suspicious keyword
        malicious_patch = "import socket\nprint('hello')"
        mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test.py"]}
        mock_analyst_instance.analyze_and_propose_patch.return_value = {"status": "success", "patch_bundle": {"file.py": malicious_patch}}

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # We use a real Coordinator and a real Verifier
            coordinator = Coordinator(repo_root=self.repo_root)
            # But we mock the test runner so it doesn't actually run tests
            with patch('tooling.test_runner.run_tests') as mock_run_tests:
                result = coordinator.run_debugging_cycle("a bug")

                # The cycle should fail because the verifier's security scan fails
                # The verifier will return 'failed', and the coordinator will escalate.
                # In this test's context, that escalation is the final failure.
                self.assertEqual(result["status"], "failed")
                self.assertIn("Security scan failed", result["message"])
                # The test runner should not have been called at all
                mock_run_tests.assert_not_called()

if __name__ == '__main__':
    unittest.main()
