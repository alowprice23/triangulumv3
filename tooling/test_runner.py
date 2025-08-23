import subprocess
import json
from pathlib import Path
import tempfile
from typing import Dict, Any
import os
import shlex

def run_test_command(
    repo_root: Path,
    command: str
) -> Dict[str, Any]:
    """
    Runs a test command in a subprocess and returns a structured JSON report.
    This runner expects the command to generate a JSON report for parsing.

    Args:
        repo_root: The root directory of the repository where the command will be run.
        command: The full test command string to execute.

    Returns:
        A dictionary containing the parsed JSON report from the test runner.
        Returns an error dictionary if the test execution fails.
    """
    # We add a placeholder to the command for the report file path.
    # The adapter is responsible for knowing where to put this placeholder.
    report_file = Path(tempfile.gettempdir()) / f"test_report_{os.getpid()}.json"

    # Replace the placeholder with the actual path.
    # This makes the runner flexible for different test frameworks (e.g., jest's --outputFile).
    final_command = command.replace("{report_file}", str(report_file))

    env = os.environ.copy()
    # Add repo_root to PYTHONPATH for Python projects. This is a bit of a
    # leaky abstraction but is a simple way to handle many Python pathing issues.
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        # Use shlex.split to handle command strings with quotes correctly
        process = subprocess.run(
            shlex.split(final_command),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        if not report_file.exists():
            return {
                "error": "Test report file not generated.",
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr
            }

        with open(report_file, 'r') as f:
            report_data = json.load(f)

        report_data["exit_code"] = process.returncode

        return report_data

    except FileNotFoundError as e:
        # This error now refers to the primary executable in the command (e.g., 'pytest', 'jest')
        return {"error": f"Command not found: {e.filename}. Is it installed and in your PATH?"}
    except json.JSONDecodeError:
        return {"error": f"Failed to parse test report JSON from {report_file}."}
    finally:
        if report_file.exists():
            report_file.unlink()
