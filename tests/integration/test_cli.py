import unittest
from unittest.mock import patch
import os
import shutil
from pathlib import Path

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
            "from ..math_ops import add\ndef test_add():\n    assert add(2, 2) == 4"
        )

    def test_scan_command(self):
        """Test the 'scan' command on a directory."""
        result = self.runner.invoke(cli, ['scan', 'agents'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("{"))
        self.assertIn("dependency_graph", result.output)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("api.openai_client.OpenAIClient.get_completion")
    def test_run_command_e2e(self, mock_get_completion):
        """
        Test the 'run' command end-to-end, mocking only the LLM call.
        """
        # The expected final content of the file, with no trailing newline
        fixed_content = "# Buggy file\ndef add(a, b):\n    return a + b"
        llm_response = f"""
I see the bug. The addition is off by one. Here is the corrected file:
```python
{fixed_content}
```
"""
        mock_get_completion.return_value = llm_response

        failing_report = {"summary": {"failed": 1}, "tests": [{"nodeid": "tests/test_math_ops.py::test_add", "outcome": "failed", "longrepr": "assert 5==4"}]}
        passing_report = {"summary": {"failed": 0}}

        with patch("agents.observer.run_tests") as mock_obs_run, \
             patch("agents.verifier.run_tests") as mock_ver_run:

            mock_obs_run.return_value = failing_report
            mock_ver_run.side_effect = [failing_report, passing_report, passing_report]

            result = self.runner.invoke(cli, [
                'run',
                '--description', 'fix the add function',
                str(self.buggy_project_dir)
            ])

            self.assertEqual(result.exit_code, 0, msg=result.output)
            self.assertIn("Result: Bug Fixed Successfully!", result.output)

            final_content = (self.buggy_project_dir / "math_ops.py").read_text()
            self.assertEqual(final_content, fixed_content)

    def tearDown(self):
        if self.buggy_project_dir.exists():
            shutil.rmtree(self.buggy_project_dir)

if __name__ == '__main__':
    unittest.main()
