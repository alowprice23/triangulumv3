import unittest
from unittest.mock import patch

from agents.meta_tuner import MetaTuner

class TestMetaTuner(unittest.TestCase):

    def setUp(self):
        self.tuner = MetaTuner()

    def test_tuner_returns_none_on_success(self):
        """Tests that the tuner returns None for a successful outcome."""
        outcome = {"status": "success"}
        llm_config = {"model_name": "test_model"}

        hint = self.tuner.tune_from_outcome(outcome, llm_config)

        self.assertIsNone(hint)

    def test_tuner_returns_hint_on_failure(self):
        """Tests that a hint string is returned after a failure."""
        failure_reason = "The patch did not compile."
        outcome = {"status": "failed", "reason": failure_reason}
        llm_config = {"model_name": "test_model"}

        hint = self.tuner.tune_from_outcome(outcome, llm_config)

        self.assertIsNotNone(hint)
        self.assertIsInstance(hint, str)
        self.assertIn("Hint:", hint)
        self.assertIn(failure_reason, hint)

if __name__ == '__main__':
    unittest.main()
