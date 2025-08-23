import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from agents.analyst import Analyst
from agents.coordinator import Coordinator
from kb.patch_motif_library import PatchMotifLibrary

class TestAdvancedAgents(unittest.TestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('api.llm_router.OpenAIClient')
    @patch('kb.patch_motif_library.PatchMotifLibrary.find_similar_motifs')
    def test_analyst_uses_kb(self, mock_find_motifs, mock_openai_client_class):
        """Test that the Analyst includes KB context in its prompt."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.get_completion.return_value = "```python\nfixed_code\n```"
        mock_openai_client_class.return_value = mock_llm_instance

        # Mock the return value from the Knowledge Base
        mock_find_motifs.return_value = [{
            "metadata": {"source_file": "old_file.py", "patch": "old_patch"}
        }]

        analyst = Analyst()
        repo_root = Path("dummy_repo")
        observer_report = {
            "failing_tests": ["tests/test_new_file.py::test_fail"],
            "logs": "error log"
        }

        with patch("pathlib.Path.read_text", return_value="file content"):
            analyst.analyze_and_propose_patch(
                observer_report,
                repo_root,
                repo_manifest=[{"path": "tests/test_new_file.py"}], # Dummy manifest
                symbol_index={} # Dummy index
            )

        # Verify the KB was queried and its context used in the prompt
        mock_find_motifs.assert_called_once()
        self.assertTrue(mock_llm_instance.get_completion.called)
        args, kwargs = mock_llm_instance.get_completion.call_args
        prompt = args[0]
        self.assertIn("Found the following similar past fixes in the Knowledge Base", prompt)
        self.assertIn("old_patch", prompt)

    @patch('agents.coordinator.Observer')
    @patch('agents.coordinator.Analyst')
    @patch('agents.coordinator.Verifier')
    @patch('agents.coordinator.PatchMotifLibrary')
    @patch('agents.coordinator.MetaTuner')
    def test_coordinator_uses_kb_and_tuner(self, mock_tuner_class, mock_kb_class, mock_verifier_class, mock_analyst_class, mock_observer_class):
        """Test that the Coordinator calls the KB and tuner on success."""
        mock_analyst_instance = mock_analyst_class.return_value
        mock_kb_instance = mock_kb_class.return_value
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
            # Mock the scanner on the coordinator instance
            coordinator.scanner = MagicMock()
            coordinator.scanner.scan.return_value = [{"path": "file.py"}, {"path": "test_file.py"}]

            coordinator.run_debugging_cycle("a bug")

        # Verify the successful fix was added to the Knowledge Base
        mock_kb_instance.add_motif.assert_called_once_with(
            patch_content="patch",
            source_file="file.py",
            error_log="error"
        )
        # Verify the meta-tuner was called
        mock_tuner_instance.tune_from_outcome.assert_called_once()

if __name__ == '__main__':
    unittest.main()
