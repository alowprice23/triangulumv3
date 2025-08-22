from pathlib import Path
import networkx as nx
from typing import Dict, Any, List, Optional
import subprocess

import tooling.test_runner
from tooling.repair import RepairTool
from tooling.fuzz_runner import FuzzRunner
from tooling.patch_bundle import apply_patch_bundle

class Verifier:
    """
    The Verifier agent applies a change and runs tests to verify the fix
    and check for regressions. It can also use advanced tools like a
    ripple effect analyzer and a fuzz tester.
    """
    def __init__(self, dependency_graph: Optional[nx.DiGraph] = None):
        self.graph = dependency_graph

    def verify_changes(
        self,
        analyst_report: Dict[str, Any],
        original_failing_tests: List[str],
        repo_root: Path,
        expect_fail: bool = False
    ) -> Dict[str, Any]:

        def _get_original_file_contents(file_paths: List[str]) -> Dict[str, str]:
            """Reads and stores the original content of files to be changed."""
            contents = {}
            for file_path in file_paths:
                full_path = repo_root / file_path
                if full_path.exists():
                    contents[file_path] = full_path.read_text()
                else:
                    contents[file_path] = None
            return contents

        def _restore_files(original_contents: Dict[str, str]):
            """Restores files to their original content."""
            print("Verifier: Restoring original file contents...")
            for file_path, content in original_contents.items():
                full_path = repo_root / file_path
                if content is not None:
                    full_path.write_text(content)
                elif full_path.exists():
                    full_path.unlink()

        patch_bundle = analyst_report.get("patch_bundle")
        if not patch_bundle:
            return {"status": "failed", "message": "No patch bundle found in analyst report."}

        files_to_change = analyst_report.get("files_changed", [])
        original_contents = _get_original_file_contents(files_to_change)

        try:
            # Apply the changes
            apply_results = apply_patch_bundle(patch_bundle, repo_root)
            if apply_results.get("failed"):
                _restore_files(original_contents)
                return {"status": "failed", "message": "Failed to apply patch bundle.", "details": apply_results["failed"]}

            # Run tests
            report = tooling.test_runner.run_tests(repo_root, test_targets=original_failing_tests)
            failed_count = report.get("summary", {}).get("failed", 0)

            # Check against expectation
            if expect_fail:
                if failed_count > 0:
                    status = "fail"
                    message = "Tests failed as expected."
                else:
                    status = "success"
                    message = "Tests passed unexpectedly."
            else:
                if failed_count == 0:
                    status = "success"
                    message = "Tests passed."
                else:
                    status = "fail"
                    message = "Tests are still failing."

            verifier_report = {
                "status": status,
                "message": message,
                "details": report
            }

            if status != "success":
                _restore_files(original_contents)

            return verifier_report

        except Exception as e:
            _restore_files(original_contents)
            raise e
