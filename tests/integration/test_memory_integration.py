import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
from pathlib import Path

from agents.analyst import Analyst
from agents.memory import Memory

class TestMemoryIntegration(unittest.TestCase):

    def setUp(self):
        self.test_project_dir = Path("temp_kb_test_project")
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)

        (self.test_project_dir / "tests").mkdir(parents=True)
        (self.test_project_dir / "math_ops.py").write_text(
            "def add(a, b):\n    return a + b + 1"
        )
        (self.test_project_dir / "tests/test_math_ops.py").write_text(
            "from math_ops import add\ndef test_add():\n    assert add(2, 2) == 4"
        )

        # Pre-populate the knowledge base with a relevant fix
        self.memory = Memory()
        self.known_patch = "--- a/math_ops.py\n+++ b/math_ops.py\n@@ -1,2 +1,2 @@\n-def add(a, b): return a + b + 1\n+def add(a, b): return a + b"
        self.known_error = "AssertionError: assert 5 == 4"
        self.memory.add_successful_fix(
            patch_content=self.known_patch,
            source_file="math_ops.py",
            error_log=self.known_error
        )
        # Give chromadb a moment to process the addition
        import time
        time.sleep(2)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('api.llm_router.OpenAIClient')
    def test_analyst_receives_memory_context(self, mock_openai_client_class):
        """
        An end-to-end test to ensure the Analyst receives and uses context
        from the Memory module.
        """
        mock_llm_instance = MagicMock()
        mock_llm_instance.get_completion.return_value = "```python\nfixed_code\n```"
        mock_openai_client_class.return_value = mock_llm_instance

        analyst = Analyst()

        observer_report = {
            "failing_tests": ["tests/test_math_ops.py::test_add"],
            "logs": self.known_error # Use the same error to ensure a match
        }

        analyst.analyze_and_propose_patch(observer_report, self.test_project_dir)

        # Assert that the prompt sent to the LLM contains the known patch
        self.assertTrue(mock_llm_instance.get_completion.called)
        args, kwargs = mock_llm_instance.get_completion.call_args
        prompt = args[0]
        self.assertIn("Found the following similar past fixes", prompt)
        self.assertIn(self.known_patch, prompt)

    def tearDown(self):
        if self.test_project_dir.exists():
            shutil.rmtree(self.test_project_dir)
        # Clean up the chromadb instance
        del self.memory

if __name__ == '__main__':
    unittest.main()
