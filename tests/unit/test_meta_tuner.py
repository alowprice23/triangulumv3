import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
import re

from agents.meta_tuner import MetaTuner

# A simplified version of the prompts file for testing
DUMMY_PROMPTS_CONTENT = """
# This is a dummy prompts file for testing.

ANALYST_PROMPT = r\"\"\"
This is the original analyst prompt.
\"\"\"

OTHER_PROMPT = r\"\"\"
Some other content.
\"\"\"
"""

class TestMetaTuner(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to act as the 'agents' folder
        self.test_dir = tempfile.mkdtemp()
        self.prompts_path = Path(self.test_dir) / "prompts.py"
        self.prompts_path.write_text(DUMMY_PROMPTS_CONTENT, encoding="utf-8")

        # Instantiate the tuner, pointing it to our dummy prompts file
        self.tuner = MetaTuner()
        self.tuner.prompts_path = self.prompts_path

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tuner_does_nothing_on_success(self):
        """Tests that the tuner does not modify the prompt on a successful outcome."""
        outcome = {"status": "success"}
        llm_config = {"model_name": "test_model"}

        original_content = self.prompts_path.read_text(encoding="utf-8")

        self.tuner.tune_from_outcome(outcome, llm_config)

        new_content = self.prompts_path.read_text(encoding="utf-8")

        self.assertEqual(original_content, new_content)

    def test_tuner_modifies_prompt_on_failure(self):
        """Tests that a hint is prepended to the prompt after a failure."""
        failure_reason = "The patch did not compile."
        outcome = {"status": "failed", "reason": failure_reason}
        llm_config = {"model_name": "test_model"}

        self.tuner.tune_from_outcome(outcome, llm_config)

        new_content = self.prompts_path.read_text(encoding="utf-8")

        self.assertIn("Hint: The previous attempt", new_content)
        self.assertIn(failure_reason, new_content)
        self.assertIn("This is the original analyst prompt.", new_content)

    def test_tuner_avoids_duplicate_hints(self):
        """Tests that the same hint is not added multiple times."""
        failure_reason = "The patch caused a new test to fail."
        outcome = {"status": "failed", "reason": failure_reason}
        llm_config = {"model_name": "test_model"}

        # Call tune twice with the same failure
        self.tuner.tune_from_outcome(outcome, llm_config)
        self.tuner.tune_from_outcome(outcome, llm_config)

        new_content = self.prompts_path.read_text(encoding="utf-8")

        # Count occurrences of the failure reason in the prompt content
        # Use regex to find the content within the ANALYST_PROMPT block
        match = re.search(r"ANALYST_PROMPT\s*=\s*r?\"\"\"(.*?)\"\"\"", new_content, re.DOTALL)
        prompt_content = match.group(1) if match else ""

        self.assertEqual(prompt_content.count(failure_reason), 1)

if __name__ == '__main__':
    unittest.main()
