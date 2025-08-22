import unittest
from unittest.mock import patch
import os
import shutil
from pathlib import Path
import traceback

from click.testing import CliRunner

from cli.main import cli

class TestCliIntegration(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.buggy_project_dir = Path("buggy_project_for_cli")
        if self.buggy_project_dir.exists():
            shutil.rmtree(self.buggy_project_dir)

        (self.buggy_project_dir / "tests").mkdir(parents=True)
        (self.buggy_project_dir / "__init__.py").touch()
        (self.buggy_project_dir / "tests/__init__.py").touch()
        (self.buggy_project_dir / "math_ops.py").write_text(
            "# Buggy file\ndef add(a, b):\n    return a + b + 1"
        )
        (self.buggy_project_dir / "tests/test_math_ops.py").write_text(
            "from math_ops import add\ndef test_add():\n    assert add(2, 2) == 4"
        )

    def test_scan_command(self):
        """Test the 'scan' command on a directory."""
        result = self.runner.invoke(cli, ['scan', 'agents'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("{"))
        self.assertIn("dependency_graph", result.output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("agents.coordinator.Coordinator.run_debugging_cycle")
    def test_run_command_e2e(self, mock_run_debugging_cycle):
        """
        Test the 'run' command end-to-end, mocking only the Coordinator's
        main loop.
        """
        # The expected final content of the file, with no trailing newline
        fixed_content = "# Buggy file\ndef add(a, b):\n    return a + b"

        # We need to simulate the successful result of the coordinator
        mock_run_debugging_cycle.return_value = {
            "status": "success",
            "patch_bundle": {"math_ops.py": "dummy_patch"},
            "llm_rationale": "The bug was fixed."
        }

        # We also need to simulate that the file was actually fixed
        def side_effect(*args, **kwargs):
            (self.buggy_project_dir / "math_ops.py").write_text(fixed_content)
            return mock_run_debugging_cycle.return_value

        mock_run_debugging_cycle.side_effect = side_effect

        result = self.runner.invoke(cli, [
            'run',
            '--description', 'fix the add function',
            str(self.buggy_project_dir)
        ], catch_exceptions=False)

        if result.exception:
            traceback.print_exception(*result.exc_info)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Result: Bug Fixed Successfully!", result.output)

        final_content = (self.buggy_project_dir / "math_ops.py").read_text()
        self.assertEqual(final_content, fixed_content)

    def tearDown(self):
        if self.buggy_project_dir.exists():
            shutil.rmtree(self.buggy_project_dir)

if __name__ == '__main__':
    unittest.main()
