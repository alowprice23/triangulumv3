import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os

# The app needs to be imported for the TestClient
from api.main import app
from api.vcs import VCSManager
from api.ci import CIManager

class TestApi(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Triangulum Agentic Bug-Fixing System API"})

    @patch("api.main.shared_state")
    def test_get_status(self, mock_shared_state):
        # ... (existing test)
        mock_supervisor = MagicMock()
        mock_supervisor.is_running = True
        mock_supervisor.scheduler.__len__.return_value = 3
        mock_supervisor.executor.get_active_session_count.return_value = 2
        mock_shared_state.get.return_value = mock_supervisor
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_running"])

    @patch("api.main.shared_state")
    def test_submit_bug(self, mock_shared_state):
        # ... (existing test)
        mock_supervisor = MagicMock()
        mock_shared_state.get.return_value = mock_supervisor
        bug_payload = {"description": "A new bug", "severity": 7}
        response = self.client.post("/bugs", json=bug_payload)
        self.assertEqual(response.status_code, 202)
        mock_supervisor.submit_bug.assert_called_once_with("A new bug", 7, code_graph=None)

    def test_metrics_endpoint(self):
        # ... (existing test)
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)

    @patch("api.main.human_review_hub")
    def test_get_reviews(self, mock_hub):
        # ... (existing test)
        mock_hub.get_pending_reviews.return_value = []
        response = self.client.get("/reviews")
        self.assertEqual(response.status_code, 200)

    @patch("api.main.human_review_hub")
    def test_make_decision(self, mock_hub):
        # ... (existing test)
        mock_hub.make_decision.return_value = True
        response = self.client.post("/reviews/bug1/decision", json={"decision": "approve"})
        self.assertEqual(response.status_code, 200)

    @patch("api.vcs.requests")
    def test_vcs_manager_post_comment(self, mock_requests):
        """Test the VCSManager via its provider, mocking the requests call."""
        os.environ["GITHUB_TOKEN"] = "test_token"
        vcs_manager = VCSManager()
        provider = vcs_manager.get_default_provider()
        self.assertIsNotNone(provider)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123}
        mock_requests.post.return_value = mock_response

        provider.post_comment("test/repo", 1, "Test comment")
        mock_requests.post.assert_called_once()

        del os.environ["GITHUB_TOKEN"]

    @patch("api.ci.requests")
    def test_ci_manager_trigger_pipeline(self, mock_requests):
        """Test the CIManager via its provider, mocking the requests call."""
        os.environ["GITHUB_TOKEN"] = "test_token"
        ci_manager = CIManager()
        provider = ci_manager.get_default_provider()
        self.assertIsNotNone(provider)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        provider.trigger_pipeline("test/repo", "my-workflow.yml", "main")
        mock_requests.post.assert_called_once()

        del os.environ["GITHUB_TOKEN"]


if __name__ == '__main__':
    unittest.main()
