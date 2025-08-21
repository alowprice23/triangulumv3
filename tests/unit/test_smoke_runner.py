import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from tooling.smoke_runner import run_smoke_tests

class TestSmokeRunner(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_smoke_dir")
        self.test_dir.mkdir()

    @patch("tooling.smoke_runner.run_tests")
    def test_smoke_runner_finds_pytest_tests(self, mock_run_tests):
        # Mock a successful pytest run with smoke tests
        mock_run_tests.return_value = {
            "summary": {"total": 5, "passed": 5},
            "exit_code": 0
        }

        result = run_smoke_tests(self.test_dir)

        self.assertEqual(result["runner"], "pytest")
        self.assertEqual(result["result"]["summary"]["total"], 5)
        mock_run_tests.assert_called_once_with(
            repo_root=self.test_dir, pytest_args=["-m", "smoke"]
        )

    @patch("tooling.smoke_runner.run_tests")
    @patch("tooling.smoke_runner.subprocess.run")
    def test_smoke_runner_falls_back_to_script(self, mock_subprocess_run, mock_run_tests):
        # Mock pytest finding no tests (exit code 5)
        mock_run_tests.return_value = {"exit_code": 5}

        # Mock a successful script run
        mock_subprocess_run.return_value = MagicMock(
            returncode=0, stdout="Smoke tests passed!", stderr=""
        )

        # Create a dummy executable script
        script_path = self.test_dir / "scripts" / "smoke.sh"
        script_path.parent.mkdir()
        script_path.touch()
        script_path.chmod(0o755)

        result = run_smoke_tests(self.test_dir)

        self.assertEqual(result["runner"], "script")
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Smoke tests passed!", result["stdout"])
        mock_subprocess_run.assert_called_once()

    @patch("tooling.smoke_runner.run_tests")
    @patch("tooling.smoke_runner.subprocess.run")
    def test_smoke_runner_no_tests_found(self, mock_subprocess_run, mock_run_tests):
        # Mock pytest finding no tests
        mock_run_tests.return_value = {"exit_code": 5}

        # No script exists, so it should find nothing
        result = run_smoke_tests(self.test_dir)

        self.assertEqual(result["runner"], "none")
        self.assertIn("No smoke tests found", result["message"])
        mock_subprocess_run.assert_not_called()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
