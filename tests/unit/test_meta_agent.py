import unittest
from unittest.mock import patch, MagicMock

from agents.meta_agent import MetaAgent

class TestMetaAgent(unittest.TestCase):

    def setUp(self):
        # The MetaAgent needs mock agents to be instantiated
        self.mock_observer = MagicMock()
        self.mock_analyst = MagicMock()
        self.mock_verifier = MagicMock()
        self.tuner = MetaAgent(self.mock_observer, self.mock_analyst, self.mock_verifier)

    def test_tuner_records_success(self):
        """Tests that the tuner correctly records a successful outcome."""
        outcome = {"status": "success", "tokens_used": 1000}

        self.tuner.record_result("bug-1", success=True, tokens_used=1000)
        self.assertEqual(len(self.tuner._hist), 1)
        self.assertTrue(self.tuner._hist[0].success)

    def test_tuner_records_failure(self):
        """Tests that the tuner correctly records a failure."""
        outcome = {"status": "failed", "tokens_used": 1500}

        self.tuner.record_result("bug-2", success=False, tokens_used=1500)
        self.assertEqual(len(self.tuner._hist), 1)
        self.assertFalse(self.tuner._hist[0].success)

if __name__ == '__main__':
    unittest.main()
