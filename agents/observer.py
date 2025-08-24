import logging
from pathlib import Path
from typing import Dict, Any, List

import tooling.test_runner
from tooling.compress import compress_text
from discovery.test_locator import SourceTestMapper
from adapters.base_adapter import LanguageAdapter

logger = logging.getLogger(__name__)

class Observer:
    """
    The Observer agent is responsible for reproducing a bug and capturing
    the initial state (e.g., failing tests, logs).
    """
    def __init__(self, adapter: LanguageAdapter):
        self.adapter = adapter
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
        logger.info("Observer: Running tests to find an initial failure...")
        # Initially, run all tests to see what fails by passing an empty list of targets.
        initial_test_command = self.adapter.get_test_command(test_targets=[])
        initial_report = tooling.test_runner.run_test_command(repo_root, initial_test_command)

        if initial_report.get("error"):
            return {"error": "Failed to run tests.", "details": initial_report}

        initial_failing_tests = [t['nodeid'] for t in initial_report.get("tests", []) if t.get("outcome") == "failed"]

        if not initial_failing_tests:
            logger.info("Observer: No failing tests found.")
            return {"status": "success", "message": "No failing tests detected.", "failing_tests": []}

        first_failing_test = initial_failing_tests[0]
        logger.info(f"Observer: Identified initial failing test: {first_failing_test}")

        # Note: The logic to find a "more comprehensive" test suite is complex
        # and language-specific. For now, we will just use the report from the
        # initial full test run. This can be enhanced later.
        final_report = initial_report

        # Process the final report
        failing_tests = [t["nodeid"] for t in final_report.get("tests", []) if t.get("outcome") == "failed"]
        full_logs = ""
        for test in final_report.get("tests", []):
            if test["outcome"] == "failed":
                full_logs += f"--- Test: {test['nodeid']} ---\n"
                full_logs += test.get("longrepr", "") + "\n"

        compressed_logs = compress_text(full_logs, max_tokens=1000)
        logger.info(f"Observer: Found {len(failing_tests)} failing tests in final report.")

        return {
            "status": "success",
            "failing_tests": failing_tests,
            "logs": compressed_logs,
            "full_report": final_report
        }
