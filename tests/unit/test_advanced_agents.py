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
        (self.repo_root / "dummy_file.py").touch()

    def tearDown(self):
        shutil.rmtree(self.repo_root)

    def test_analyst_uses_kb(self):
        """Test that the Analyst includes KB context in its prompt."""
        with patch('agents.analyst.LLMConfig') as mock_llm_config_class, \
             patch('kb.patch_motif_library.PatchMotifLibrary.find_similar_motifs') as mock_find_motifs:

            mock_llm_instance = MagicMock()
            mock_llm_instance.get_completion.return_value = "```python\nfixed_code\n```"

            mock_llm_config_instance = mock_llm_config_class.return_value
            mock_llm_config_instance.get_client.return_value = mock_llm_instance

            mock_find_motifs.return_value = [{"metadata": {"source_file": "old.py", "patch": "p"}}]

            analyst = Analyst()

            # Create a dummy code graph to provide context
            from discovery.code_graph import CodeGraph, CodeGraphFile
            dummy_file = CodeGraphFile(path="dummy_file.py", hash="", loc=0)
            dummy_code_graph = CodeGraph(language="Python", manifest=[dummy_file])

            with patch("pathlib.Path.read_text", return_value="content"), \
                 patch("discovery.test_locator.SourceTestMapper.map_test_to_source", return_value="dummy_source.py"):
                analyst.analyze_and_propose_patch({"failing_tests": ["t.py"], "logs": "e"}, self.repo_root, dummy_code_graph)

            self.assertTrue(mock_llm_instance.get_completion.called)
            self.assertIn("Knowledge Base", mock_llm_instance.get_completion.call_args[0][0])

    def test_coordinator_uses_kb_and_tuner_on_success(self):
        """Test that the Coordinator calls the KB and tuner on a successful run."""
        with patch('agents.coordinator.request_human_feedback'), \
             patch('agents.coordinator.Observer') as mock_observer_class, \
             patch('agents.coordinator.Analyst') as mock_analyst_class, \
             patch('agents.coordinator.PatchMotifLibrary') as mock_kb_class, \
             patch('agents.meta_agent.MetaAgent') as mock_meta_agent_class, \
             patch('agents.coordinator.Verifier') as mock_verifier_class, \
             patch('runtime.performance_logger.PerformanceLogger.log_session'):

            mock_analyst_instance = mock_analyst_class.return_value
            mock_kb_instance = mock_kb_class.return_value
            mock_meta_agent_instance = mock_meta_agent_class.return_value
            mock_observer_instance = mock_observer_class.return_value
            mock_verifier_instance = mock_verifier_class.return_value

            mock_analyst_instance.llm_config.provider = "openai"
            mock_analyst_instance.llm_config.model_name = "test-model"

            mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test.py"]}
            mock_analyst_instance.analyze_and_propose_patch.return_value = {"status": "success", "patch_bundle": {"file.py": "patch"}, "original_error_log": "error"}
            mock_verifier_instance.verify_changes.side_effect = [{"status": "fail"}, {"status": "success"}]

            coordinator = Coordinator(repo_root=self.repo_root)

            # Create a dummy code graph to bypass language probing
            from discovery.code_graph import CodeGraph, CodeGraphFile
            dummy_file = CodeGraphFile(path="dummy_file.py", hash="", loc=0)
            dummy_code_graph = CodeGraph(language="Python", manifest=[dummy_file])

            result = coordinator.run_debugging_cycle("a bug", code_graph=dummy_code_graph)
            print("Coordinator result:", result)

            # The coordinator should have added the successful patch to the KB
            mock_kb_instance.add_motif.assert_called_once()

    def test_verifier_rejects_malicious_patch(self):
        """Test that a malicious patch from the Analyst is caught and rejected."""
        with patch('agents.coordinator.request_human_feedback') as mock_request_human_feedback, \
             patch('discovery.repo_scanner.RepoScanner') as mock_repo_scanner_class, \
             patch('agents.coordinator.Observer') as mock_observer_class, \
             patch('agents.coordinator.Analyst') as mock_analyst_class, \
             patch('agents.coordinator.LLMConfig') as mock_llm_config_class:

            mock_request_human_feedback.return_value = "user hint"
            mock_repo_scanner_instance = mock_repo_scanner_class.return_value
            mock_repo_scanner_instance.scan.return_value = [{"path": "file.py"}]
            mock_observer_instance = mock_observer_class.return_value
            mock_analyst_instance = mock_analyst_class.return_value
            mock_analyst_instance.llm_config.provider = "openai"
            mock_analyst_instance.llm_config.model_name = "test-model"

            mock_llm_instance = MagicMock()
            mock_llm_config_instance = mock_llm_config_class.return_value
            mock_llm_config_instance.get_client.return_value = mock_llm_instance

            # The analyst proposes a patch containing a suspicious keyword
            malicious_patch = "import socket\nprint('hello')"
            mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test.py"]}
            mock_analyst_instance.analyze_and_propose_patch.return_value = {"status": "success", "patch_bundle": {"file.py": malicious_patch}}

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                # We use a real Coordinator and a real Verifier
                coordinator = Coordinator(repo_root=self.repo_root)

            # Create a dummy code graph to bypass language probing
            from discovery.code_graph import CodeGraph, CodeGraphFile
            dummy_file = CodeGraphFile(path="dummy_file.py", hash="", loc=0)
            dummy_code_graph = CodeGraph(language="Python", manifest=[dummy_file])

            # But we mock the test runner so it doesn't actually run tests
            with patch('tooling.test_runner.run_tests') as mock_run_tests:
                result = coordinator.run_debugging_cycle("a bug", code_graph=dummy_code_graph)

                # The cycle should fail because the verifier's security scan fails
                # The verifier will return 'failed', and the coordinator will escalate.
                # In this test's context, that escalation is the final failure.
                self.assertEqual(result["status"], "failed")
                self.assertIn("Security scan failed", result["message"])
                # The test runner should not have been called at all
                mock_run_tests.assert_not_called()

if __name__ == '__main__':
    unittest.main()
