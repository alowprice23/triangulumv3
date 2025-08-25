"""
The Human-in-the-Loop (HITL) Review Hub.

This module manages the queue of items that require human review and intervention.
When the autonomous system cannot resolve a bug or requires approval for a risky
patch, the bug is escalated to this hub. This implementation provides an in-memory
queue and is designed to be accessed via a web API.
"""

import threading
from typing import List, Dict, Any, Optional

class ReviewItem:
    """Represents a single item in the review queue."""
    def __init__(self, bug_id: str, patch_proposal: Dict[str, Any], reason: str):
        self.bug_id = bug_id
        self.patch_proposal = patch_proposal
        self.reason = reason
        self.status = "pending"  # pending, approved, rejected
        self.decision = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "patch_proposal": self.patch_proposal,
            "reason": self.reason,
            "status": self.status,
        }

class HumanReviewHub:
    """
    Manages the queue of review items and handles human decisions.
    This is a simple in-memory implementation.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._reviews: Dict[str, ReviewItem] = {}
        self._decision_callbacks = []

    def add_review_item(self, bug_id: str, patch_proposal: Dict[str, Any], reason: str):
        """Adds a new item to the review queue."""
        with self._lock:
            if bug_id in self._reviews:
                return # Avoid duplicate entries

            item = ReviewItem(bug_id, patch_proposal, reason)
            self._reviews[bug_id] = item

    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Returns a list of all items currently pending review."""
        with self._lock:
            return [
                item.to_dict() for item in self._reviews.values()
                if item.status == "pending"
            ]

    def make_decision(self, bug_id: str, decision: str) -> bool:
        """
        Records a human's decision on a review item.
        'decision' can be 'approve' or 'reject'.
        """
        with self._lock:
            item = self._reviews.get(bug_id)
            if not item or item.status != "pending":
                return False

            if decision == "approve":
                item.status = "approved"
            elif decision == "reject":
                item.status = "rejected"
            else:
                return False # Invalid decision

            item.decision = decision

            # Notify any listeners (like the supervisor) about the decision
            for callback in self._decision_callbacks:
                callback(bug_id, decision)

            return True

    def subscribe_to_decisions(self, callback):
        """Allows other components (like the supervisor) to be notified of decisions."""
        self._decision_callbacks.append(callback)

# A global instance of the hub to be shared across the application.
# This is a simple approach for a single-process application.
hub = HumanReviewHub()
