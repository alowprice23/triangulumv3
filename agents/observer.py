from pathlib import Path
from typing import Dict, Any, List

import tooling.test_runner
from tooling.compress import compress_text
from discovery.test_locator import SourceTestMapper

class Observer:
    """
    The Observer agent is responsible for reproducing a bug and capturing
    the initial state (e.g., failing tests, logs).
    """
    def __init__(self):
        self.test_mapper = SourceTestMapper()

    def observe_bug(
        self,
        repo_root: Path,
        file_scope: List[str] = None
    ) -> Dict[str, Any]:
        """
        Runs tests to find a failure, then uses the TestLocator to run a
        more focused test suite to gather comprehensive information.
        """
        print("Observer: Running tests to find an initial failure...")
        initial_report = tooling.test_runner.run_tests(repo_root, test_targets=file_scope)

        if initial_report.get("error"):
            return {"error": "Failed to run tests.", "details": initial_report}

        initial_failing_tests = [t['nodeid'] for t in initial_report.get("tests", []) if t.get("outcome") == "failed"]

        if not initial_failing_tests:
            print("Observer: No failing tests found.")
            return {"status": "success", "message": "No failing tests detected.", "failing_tests": []}

        first_failing_test = initial_failing_tests[0]
        print(f"Observer: Identified initial failing test: {first_failing_test}")

        # Use the TestLocator to find a more comprehensive test suite
        try:
            source_file = first_failing_test.split("::")[0].replace("tests/test_", "test_")
        except IndexError:
            source_file = None

        if source_file:
            print(f"Observer: Locating all tests for source file: {source_file}")
            comprehensive_test_suite = self.test_mapper.find_tests_for_source(source_file, file_scope, repo_root)
        else:
            comprehensive_test_suite = []

        if not comprehensive_test_suite:
            print("Observer: Could not locate a specific test suite. Using initial failure report.")
            final_report = initial_report
        else:
            print(f"Observer: Running comprehensive test suite: {comprehensive_test_suite}")
            final_report = tooling.test_runner.run_tests(repo_root, comprehensive_test_suite)

        # Process the final report
        failing_tests = [t["nodeid"] for t in final_report.get("tests", []) if t.get("outcome") == "failed"]
        full_logs = ""
        for test in final_report.get("tests", []):
            if test["outcome"] == "failed":
                full_logs += f"--- Test: {test['nodeid']} ---\n"
                full_logs += test.get("longrepr", "") + "\n"

        compressed_logs = compress_text(full_logs, max_tokens=1000)
        print(f"Observer: Found {len(failing_tests)} failing tests in final report.")

        return {
            "status": "success",
            "failing_tests": failing_tests,
            "logs": compressed_logs,
            "full_report": final_report
        }
