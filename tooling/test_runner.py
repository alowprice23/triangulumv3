import subprocess
import json
from pathlib import Path
import tempfile
from typing import List, Dict, Any, Optional
import os

def run_tests(
    repo_root: Path,
    test_targets: Optional[List[str]] = None,
    pytest_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Runs tests using pytest and returns a structured JSON report.

    Args:
        repo_root: The root directory of the repository where tests will be run.
        test_targets: A list of specific test files or directories to run.
                      If empty, runs all tests discovered by pytest.
        pytest_args: A list of additional arguments to pass to pytest (e.g., ["-m", "smoke"]).

    Returns:
        A dictionary containing the parsed JSON report from pytest.
        Returns an error dictionary if the test execution fails.
    """
    report_file = Path(tempfile.gettempdir()) / f"test_report_{os.getpid()}.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

    command = [
        "pytest",
        "-p", "no:cacheprovider", # Disable the cache to ensure fresh runs
        "--json-report",
        f"--json-report-file={report_file}",
        "--json-report-summary"
    ]

    if pytest_args:
        command.extend(pytest_args)

    if test_targets:
        command.extend(test_targets)

    try:
        process = subprocess.run(
            command,
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

    except FileNotFoundError:
        return {"error": "'pytest' command not found. Is it installed and in your PATH?"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse test report JSON."}
    finally:
        if report_file.exists():
            report_file.unlink()
