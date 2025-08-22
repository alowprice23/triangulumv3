import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from agents.analyst import Analyst
from agents.coordinator import Coordinator
from agents.memory import Memory

class TestAdvancedAgents(unittest.TestCase):

    @patch('agents.memory.PatchMotifLibrary')
    def test_memory_add_fix(self, mock_patch_library_class):
        """Test that the Memory module calls the underlying KB library."""
        mock_library_instance = MagicMock()
        mock_patch_library_class.return_value = mock_library_instance

        memory = Memory()
        memory.add_successful_fix("patch", "file.py", "error")

        mock_library_instance.add_motif.assert_called_once_with(
            patch_content="patch",
            source_file="file.py",
            error_log="error"
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('api.llm_router.OpenAIClient') # Corrected patch target
    @patch('agents.memory.Memory.find_similar_fixes')
    def test_analyst_uses_memory(self, mock_find_fixes, mock_openai_client_class):
        """Test that the Analyst includes memory context in its prompt."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.get_completion.return_value = "```python\nfixed_code\n```"
        # When OpenAIClient is instantiated in the router, it will be this mock
        mock_openai_client_class.return_value = mock_llm_instance

        mock_find_fixes.return_value = [{
            "metadata": {"source_file": "old_file.py", "patch": "old_patch"}
        }]

        analyst = Analyst()

        repo_root = Path("dummy_repo")
        observer_report = {
            "failing_tests": ["tests/test_new_file.py::test_fail"],
            "logs": "error log"
        }

        with patch("pathlib.Path.read_text", return_value="file content"):
            analyst.analyze_and_propose_patch(observer_report, repo_root)

        self.assertTrue(mock_llm_instance.get_completion.called)
        args, kwargs = mock_llm_instance.get_completion.call_args
        prompt = args[0]
        self.assertIn("Found the following similar past fixes", prompt)
        self.assertIn("old_patch", prompt)

    @patch('agents.coordinator.Observer')
    @patch('agents.coordinator.Analyst')
    @patch('agents.coordinator.Verifier')
    @patch('agents.coordinator.Memory')
    @patch('agents.coordinator.MetaTuner')
    def test_coordinator_uses_memory_and_tuner(self, mock_tuner_class, mock_memory_class, mock_verifier_class, mock_analyst_class, mock_observer_class):
        """Test that the Coordinator calls memory and tuner on success."""
        mock_analyst_instance = mock_analyst_class.return_value
        mock_memory_instance = mock_memory_class.return_value
        mock_tuner_instance = mock_tuner_class.return_value
        mock_observer_instance = mock_observer_class.return_value
        mock_verifier_instance = mock_verifier_class.return_value

        mock_observer_instance.observe_bug.return_value = {"status": "success", "failing_tests": ["test.py"]}
        mock_analyst_instance.analyze_and_propose_patch.return_value = {
            "status": "success",
            "patch_bundle": {"file.py": "patch"},
            "original_error_log": "error",
            "files_changed": ["file.py"]
        }
        mock_verifier_instance.verify_changes.side_effect = [
            {"status": "fail"},
            {"status": "success"}
        ]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            coordinator = Coordinator(repo_root=Path("."))
            coordinator.run_debugging_cycle("a bug", initial_scope=["file.py", "test_file.py"])

        mock_memory_instance.add_successful_fix.assert_called_once_with(
            patch_content="patch",
            source_file="file.py",
            error_log="error"
        )
        mock_tuner_instance.tune_from_outcome.assert_called_once()


if __name__ == '__main__':
    unittest.main()
