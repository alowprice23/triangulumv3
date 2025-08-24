import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# The app needs to be imported for the TestClient
from api.main import app

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
        """Test the /status endpoint."""
        # Mock the supervisor instance that the endpoint will get
        mock_supervisor = MagicMock()
        mock_supervisor.is_running = True
        # Mock the scheduler's length
        mock_supervisor.scheduler.__len__.return_value = 3
        # Mock the executor's count
        mock_supervisor.executor.get_active_session_count.return_value = 2

        mock_shared_state.get.return_value = mock_supervisor

        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["is_running"])
        self.assertEqual(data["queued_tickets"], 3)
        self.assertEqual(data["active_sessions"], 2)

    @patch("api.main.shared_state")
    def test_submit_bug(self, mock_shared_state):
        """Test the /bugs endpoint."""
        mock_supervisor = MagicMock()
        mock_shared_state.get.return_value = mock_supervisor

        bug_payload = {"description": "A new bug", "severity": 7}
        response = self.client.post("/bugs", json=bug_payload)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"message": "Bug ticket submitted successfully."})

        # Verify that the supervisor's method was called correctly
        mock_supervisor.submit_bug.assert_called_once_with("A new bug", 7, code_graph=None)

    def test_metrics_endpoint(self):
        """Test the /metrics endpoint."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.headers["content-type"])
        self.assertIn("python_info", response.text)

if __name__ == '__main__':
    unittest.main()
