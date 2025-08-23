import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import shutil
from pathlib import Path
import traceback
import time

from click.testing import CliRunner

from cli.main import cli
from runtime.supervisor import Supervisor

class TestCliIntegration(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.buggy_project_dir = Path("buggy_project_for_cli")
        if self.buggy_project_dir.exists():
            shutil.rmtree(self.buggy_project_dir)

        # Create a dummy project structure
        (self.buggy_project_dir / "tests").mkdir(parents=True)
        (self.buggy_project_dir / "__init__.py").touch()
        (self.buggy_project_dir / "tests/__init__.py").touch()
        (self.buggy_project_dir / "math_ops.py").write_text(
            "# Buggy file\ndef add(a, b):\n    return a + b + 1"
        )
        (self.buggy_project_dir / "tests/test_math_ops.py").write_text(
            "from math_ops import add\ndef test_add():\n    assert add(2, 2) == 4"
        )

    def tearDown(self):
        if self.buggy_project_dir.exists():
            shutil.rmtree(self.buggy_project_dir)

    def test_scan_command(self):
        """Test the 'scan' command on a directory."""
        result = self.runner.invoke(cli, ['scan', 'agents'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("{"))
        self.assertIn("dependency_graph", result.output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('cli.commands.run.Supervisor')
    def test_run_command_invokes_supervisor(self, mock_supervisor_class):
        """
        Test that the 'run' command correctly instantiates and starts the Supervisor.
        """
        mock_supervisor_instance = MagicMock(spec=Supervisor)
        mock_supervisor_class.return_value = mock_supervisor_instance

        result = self.runner.invoke(cli, [
            'run',
            '--description', 'fix the add function',
            '--severity', '8',
            '--duration', '30',
            str(self.buggy_project_dir)
        ], catch_exceptions=False)

        self.assertEqual(result.exit_code, 0, msg=result.output)

        # Verify Supervisor was instantiated correctly
        mock_supervisor_class.assert_called_once_with(
            max_concurrent_sessions=3,
            repo_root=self.buggy_project_dir.resolve()
        )

        # Verify submit_bug and run were called correctly
        mock_supervisor_instance.submit_bug.assert_called_once_with('fix the add function', 8)
        mock_supervisor_instance.run.assert_called_once_with(duration_seconds=30)
        self.assertIn("Supervisor has finished its run.", result.output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('runtime.supervisor.ParallelExecutor')
    def test_run_command_e2e_simulation(self, mock_parallel_executor_class):
        """
        Test the 'run' command end-to-end by simulating a successful bug fix
        through a mocked ParallelExecutor.
        """
        fixed_content = "# Buggy file\ndef add(a, b):\n    return a + b"
        mock_executor_instance = MagicMock()
        mock_parallel_executor_class.return_value = mock_executor_instance

        # This side effect simulates the file being fixed upon launch
        def launch_side_effect(ticket, repo_root):
            # Simulate the file being fixed
            (self.buggy_project_dir / "math_ops.py").write_text(fixed_content)
            # Simulate a successful launch
            return True

        # This simulates the check for completed sessions
        def check_side_effect():
            # After the first check, report the session as completed
            if not hasattr(check_side_effect, "called"):
                check_side_effect.called = True
                return []
            return [("mock_bug_id", {"status": "success"})]

        mock_executor_instance.launch_session.side_effect = launch_side_effect
        mock_executor_instance.check_completed_sessions.side_effect = check_side_effect
        mock_executor_instance.get_active_session_count.return_value = 0

        # Run the command for a very short duration (e.g., 6 seconds to allow 2 ticks)
        result = self.runner.invoke(cli, [
            'run',
            '--description', 'fix the add function',
            '--duration', '6', # Allows for two 5-second ticks
            str(self.buggy_project_dir)
        ], catch_exceptions=False)

        if result.exception:
            traceback.print_exception(*result.exc_info)

        self.assertEqual(result.exit_code, 0, msg=result.output)

        # Verify that the supervisor logged the completion
        self.assertIn("finished with status: success", result.output)

        # Verify the file was actually fixed
        final_content = (self.buggy_project_dir / "math_ops.py").read_text()
        self.assertEqual(final_content, fixed_content)

if __name__ == '__main__':
    unittest.main()
