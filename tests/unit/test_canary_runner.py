import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import requests # <--- ADD THIS IMPORT

from tooling.canary_runner import start_canary, stop_canary

class TestCanaryRunner(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_canary_dir")
        self.test_dir.mkdir()
        (self.test_dir / "docker-compose.yml").touch()

    @patch("tooling.canary_runner.subprocess.run")
    @patch("tooling.canary_runner.requests.get")
    def test_start_canary_success(self, mock_requests_get, mock_subprocess_run):
        # Mock a successful docker-compose up
        mock_subprocess_run.return_value = MagicMock(returncode=0, stderr="")
        # Mock a successful health check
        mock_requests_get.return_value = MagicMock(status_code=200)

        success, message = start_canary(self.test_dir)
        self.assertTrue(success)
        self.assertIn("healthy", message)
        mock_subprocess_run.assert_called_with(
            ["docker-compose", "up", "-d", "--build"],
            cwd=self.test_dir, check=True, capture_output=True, text=True
        )

    @patch("tooling.canary_runner.subprocess.run")
    def test_start_canary_docker_compose_fails(self, mock_subprocess_run):
        # Mock a failed docker-compose up
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Docker error")

        success, message = start_canary(self.test_dir)
        self.assertFalse(success)
        self.assertIn("docker-compose up failed", message)

    @patch("tooling.canary_runner.subprocess.run")
    @patch("tooling.canary_runner.requests.get")
    @patch("tooling.canary_runner.time.sleep", return_value=None) # Patch sleep to speed up test
    def test_start_canary_health_check_fails(self, mock_sleep, mock_requests_get, mock_subprocess_run):
        # Mock a successful docker-compose up but a failing health check
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stderr=""), # For the 'up' call
            MagicMock(returncode=0, stderr="")  # For the 'down' call during cleanup
        ]
        mock_requests_get.side_effect = requests.exceptions.ConnectionError()

        success, message = start_canary(self.test_dir)
        self.assertFalse(success)
        self.assertIn("Health check failed", message)
        self.assertEqual(mock_requests_get.call_count, 10) # 10 retries

    def test_start_canary_no_docker_compose_file(self):
        (self.test_dir / "docker-compose.yml").unlink()
        success, message = start_canary(self.test_dir)
        self.assertFalse(success)
        self.assertIn("not found", message)

    @patch("tooling.canary_runner.subprocess.run")
    def test_stop_canary_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        success, message = stop_canary(self.test_dir)
        self.assertTrue(success)
        self.assertIn("stopped successfully", message)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
