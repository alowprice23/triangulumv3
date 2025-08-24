import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

def run_tests(repo_root: Path, test_targets: List[str] = None, pytest_args: List[str] = None) -> Dict[str, Any]:
    """
    Runs pytest on specified test targets within the repository and returns a
    structured JSON report.

    Args:
        repo_root: The root directory of the repository where the tests will be run.
        test_targets: A list of specific test files or directories to run. If None,
                      runs tests in the entire repository.
        pytest_args: A list of additional arguments to pass to pytest.

    Returns:
        A dictionary containing the test results.
    """
    if test_targets is None:
        test_targets = [str(repo_root)]
    if pytest_args is None:
        pytest_args = []

    report_path = "test_report.json"
    report_file_abs = Path(repo_root) / report_path
    command = [
        sys.executable,
        "-m",
        "pytest",
        *test_targets,
        f"--json-report-file={report_path}",
    ] + pytest_args

    try:
        process = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if report_file_abs.exists():
            with open(report_file_abs, "r") as f:
                report_data = json.load(f)
            report_file_abs.unlink()
        else:
            # If no report is generated, it's likely because no tests were
            # collected. We can create a synthetic report.
            report_data = {
                "summary": {"total": 0, "passed": 0, "failed": 0},
                "tests": [],
                "stdout": process.stdout,
                "stderr": process.stderr,
            }

        report_data["exit_code"] = process.returncode
        return report_data

    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
