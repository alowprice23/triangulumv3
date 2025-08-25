import unittest
from unittest.mock import Mock

from runtime.human_hub import HumanReviewHub

class TestHumanReviewHub(unittest.TestCase):

    def setUp(self):
        """Create a new HumanReviewHub instance for each test."""
        self.hub = HumanReviewHub()

    def test_add_and_get_review_item(self):
        """Test that an item can be added and retrieved."""
        self.assertEqual(len(self.hub.get_pending_reviews()), 0)
        self.hub.add_review_item("bug1", {"content": "patch1"}, "Reason 1")
        pending = self.hub.get_pending_reviews()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["bug_id"], "bug1")
        self.assertEqual(pending[0]["reason"], "Reason 1")

    def test_add_duplicate_item(self):
        """Test that adding a duplicate item is ignored."""
        self.hub.add_review_item("bug1", {"content": "patch1"}, "Reason 1")
        self.hub.add_review_item("bug1", {"content": "patch2"}, "Reason 2")
        self.assertEqual(len(self.hub.get_pending_reviews()), 1)

    def test_make_decision_approve(self):
        """Test the 'approve' decision workflow."""
        self.hub.add_review_item("bug1", {}, "Reason")
        self.assertTrue(self.hub.make_decision("bug1", "approve"))
        # The item should no longer be pending
        self.assertEqual(len(self.hub.get_pending_reviews()), 0)

    def test_make_decision_reject(self):
        """Test the 'reject' decision workflow."""
        self.hub.add_review_item("bug1", {}, "Reason")
        self.assertTrue(self.hub.make_decision("bug1", "reject"))
        self.assertEqual(len(self.hub.get_pending_reviews()), 0)

    def test_make_decision_invalid_bug_id(self):
        """Test making a decision for a non-existent bug ID."""
        self.assertFalse(self.hub.make_decision("nonexistent", "approve"))

    def test_make_decision_invalid_decision(self):
        """Test making an invalid decision string."""
        self.hub.add_review_item("bug1", {}, "Reason")
        self.assertFalse(self.hub.make_decision("bug1", "invalid_decision"))
        # The item should still be pending
        self.assertEqual(len(self.hub.get_pending_reviews()), 1)

    def test_decision_callback(self):
        """Test that the decision callback is fired correctly."""
        mock_callback = Mock()
        self.hub.subscribe_to_decisions(mock_callback)

        self.hub.add_review_item("bug1", {}, "Reason")
        self.hub.make_decision("bug1", "approve")

        mock_callback.assert_called_once_with("bug1", "approve")

if __name__ == '__main__':
    unittest.main()
