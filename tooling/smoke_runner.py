import subprocess
from pathlib import Path
from typing import Dict, Any

from tooling.test_runner import run_tests

def run_smoke_tests(repo_root: Path) -> Dict[str, Any]:
    """
    Runs smoke tests for a repository.

    It first tries to run pytest with the 'smoke' marker.
    If no tests are found, it falls back to executing a shell script.

    Args:
        repo_root: The root directory of the repository.

    Returns:
        A dictionary containing the test results.
    """
    # 1. Try pytest with marker
    pytest_result = run_tests(repo_root=repo_root, pytest_args=["-m", "smoke"])

    # Pytest exit code 5 means no tests were collected
    if pytest_result.get("exit_code") != 5:
        return {
            "runner": "pytest",
            "result": pytest_result
        }

    # 2. Fallback to shell script
    possible_scripts = ["scripts/smoke.sh", "smoke-tests.sh", "tests/smoke.sh"]
    for script_name in possible_scripts:
        script_path = repo_root / script_name
        if script_path.is_file() and script_path.stat().st_mode & 0o111: # Check if executable
            try:
                process = subprocess.run(
                    [str(script_path)],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                return {
                    "runner": "script",
                    "script": script_name,
                    "exit_code": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
            except Exception as e:
                return {"runner": "script", "error": str(e)}

    return {
        "runner": "none",
        "message": "No smoke tests found (pytest marker 'smoke' or known script)."
    }
