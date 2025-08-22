from pathlib import Path
from typing import Dict, Any, List

import tooling.test_runner
from tooling.compress import compress_text

class Observer:
    """
    The Observer agent is responsible for reproducing a bug and capturing
    the initial state (e.g., failing tests, logs).
    """

    def observe_bug(
        self,
        repo_root: Path,
        test_targets: List[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the test suite to find failing tests and capture their output.

        Args:
            repo_root: The root path of the repository.
            test_targets: Specific tests to run. If None, runs all.

        Returns:
            A dictionary (the "Observer Report") containing the findings.
        """
        print("Observer: Running tests to reproduce the bug...")

        report = tooling.test_runner.run_tests(repo_root, test_targets=test_targets)

        if report.get("error"):
            print(f"Observer: Error running tests: {report['error']}")
            return {"error": "Failed to run tests.", "details": report}

        failing_tests = []
        full_logs = ""

        if "tests" in report:
            for test in report["tests"]:
                if test["outcome"] == "failed":
                    failing_tests.append(test["nodeid"])
                    full_logs += f"--- Test: {test['nodeid']} ---\n"
                    full_logs += test.get("longrepr", "") + "\n"

        if not failing_tests:
            print("Observer: No failing tests found.")
            return {"status": "success", "message": "No failing tests detected."}

        # Compress the logs to a reasonable size
        compressed_logs = compress_text(full_logs, max_tokens=1000)

        print(f"Observer: Found {len(failing_tests)} failing tests.")

        return {
            "status": "success",
            "failing_tests": failing_tests,
            "logs": compressed_logs,
            "full_report": report
        }
