import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import shutil
from pathlib import Path
import traceback
import time
from concurrent.futures import Future

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

    @patch('cli.commands.scan.probe_language')
    @patch('cli.commands.scan.get_language_adapter')
    @patch('cli.commands.scan.CodeGraphBuilder')
    def test_scan_command(self, mock_code_graph_builder_class, mock_get_language_adapter, mock_probe_language):
        """Test the 'scan' command on a directory."""
        # Mock the dependencies
        mock_probe_language.return_value = "Python"
        mock_adapter = MagicMock()
        mock_get_language_adapter.return_value = mock_adapter
        mock_builder_instance = MagicMock()
        mock_code_graph_builder_class.return_value = mock_builder_instance
        mock_code_graph = MagicMock()
        mock_code_graph.dict.return_value = {"metadata": {}, "manifest": [], "symbol_index": {}, "dependency_graph": {}}
        mock_builder_instance.build.return_value = mock_code_graph

        # Run the command
        result = self.runner.invoke(cli, ['scan', str(self.buggy_project_dir)])

        # Assert the results
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("{"))
        self.assertIn("dependency_graph", result.output)

        # Assert that the mocks were called correctly
        mock_probe_language.assert_called_once()
        mock_get_language_adapter.assert_called_once_with("python")
        mock_code_graph_builder_class.assert_called_once_with(repo_root=self.buggy_project_dir, adapter=mock_adapter)
        mock_builder_instance.build.assert_called_once()

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
    def test_run_command_e2e_simulation(self):
        """
        Test the 'run' command end-to-end.
        """
        # Run the command
        result = self.runner.invoke(cli, [
            'run',
            '--description', 'fix the add function in math_ops.py',
            '--duration', '60',
            str(self.buggy_project_dir)
        ], catch_exceptions=False)

        if result.exception:
            traceback.print_exception(*result.exc_info)

        self.assertEqual(result.exit_code, 0, msg=result.output)

        # Verify that the bug was fixed
        fixed_content = (self.buggy_project_dir / "math_ops.py").read_text()
        self.assertIn("return a + b", fixed_content)

    @patch('cli.commands.interactive.check_api_status')
    @patch('cli.commands.interactive.start_analysis_session')
    @patch('cli.commands.interactive.submit_bug')
    @patch('cli.commands.interactive.monitor_progress')
    def test_interactive_command(self, mock_monitor_progress, mock_submit_bug, mock_start_analysis_session, mock_check_api_status):
        """Test the 'interactive' command."""
        # Mock the functions called by the interactive command
        mock_check_api_status.return_value = True
        mock_start_analysis_session.return_value = "test-session-id"
        mock_submit_bug.return_value = True

        # Run the command with input
        result = self.runner.invoke(
            cli,
            ['interactive', str(self.buggy_project_dir)],
            input="A test bug\n5\n",
            catch_exceptions=False
        )

        # Check that the command ran successfully
        self.assertEqual(result.exit_code, 0, msg=result.output)

        # Verify that the mocked functions were called correctly
        mock_check_api_status.assert_called_once()
        mock_start_analysis_session.assert_called_once_with(str(self.buggy_project_dir.resolve()))
        mock_submit_bug.assert_called_once_with("A test bug", 5, "test-session-id")
        mock_monitor_progress.assert_called_once()

if __name__ == '__main__':
    unittest.main()
