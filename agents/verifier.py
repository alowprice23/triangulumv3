from pathlib import Path
from typing import Dict, Any, List

from tooling.test_runner import run_tests

class Verifier:
    """
    The Verifier agent applies a change and runs tests to verify the fix
    and check for regressions.
    """

    def _get_original_file_contents(self, repo_root: Path, file_paths: List[str]) -> Dict[str, str]:
        """Reads and stores the original content of files to be changed."""
        contents = {}
        for file_path in file_paths:
            full_path = repo_root / file_path
            if full_path.exists():
                contents[file_path] = full_path.read_text()
            else:
                contents[file_path] = None # File will be newly created
        return contents

    def _restore_files(self, repo_root: Path, original_contents: Dict[str, str]):
        """Restores files to their original content."""
        print("Verifier: Restoring original file contents...")
        for file_path, content in original_contents.items():
            full_path = repo_root / file_path
            if content is not None:
                full_path.write_text(content)
            elif full_path.exists():
                # If the file did not exist before, remove it
                full_path.unlink()


    def verify_changes(
        self,
        analyst_report: Dict[str, Any],
        original_failing_tests: List[str],
        repo_root: Path
    ) -> Dict[str, Any]:
        """
        Applies and verifies file changes.

        Args:
            analyst_report: The report from the Analyst, containing the modified files.
            original_failing_tests: The list of tests that were failing.
            repo_root: The root path of the repository.

        Returns:
            A dictionary containing the verification results.
        """
        modified_files = analyst_report.get("modified_files")
        if not modified_files:
            return {"status": "failed", "message": "No modified files found in analyst report."}

        files_to_change = list(modified_files.keys())
        original_contents = self._get_original_file_contents(repo_root, files_to_change)

        try:
            # 1. Confirm tests are still failing (fail-first)
            print("Verifier: Confirming tests are failing before applying changes...")
            pre_patch_report = run_tests(repo_root, test_targets=original_failing_tests)
            if pre_patch_report.get("summary", {}).get("failed", 0) == 0:
                self._restore_files(repo_root, original_contents)
                return {"status": "failed", "message": "Tests were not failing before applying changes."}

            # 2. Apply the changes by overwriting files
            print("Verifier: Applying changes by overwriting files...")
            for file_path, new_content in modified_files.items():
                (repo_root / file_path).write_text(new_content)

            # 3. Confirm fix (pass-second)
            print("Verifier: Confirming fix after applying changes...")
            post_patch_report = run_tests(repo_root, test_targets=original_failing_tests)
            if post_patch_report.get("summary", {}).get("failed", 0) > 0:
                self._restore_files(repo_root, original_contents)
                return {"status": "failed", "message": "Tests are still failing after applying changes."}

            # 4. Check for regressions
            print("Verifier: Checking for regressions...")
            regression_report = run_tests(repo_root) # Run all tests
            if regression_report.get("summary", {}).get("failed", 0) > 0:
                self._restore_files(repo_root, original_contents)
                return {"status": "failed", "message": "Changes introduced regressions.", "details": regression_report}

            print("Verifier: Changes verified successfully!")
            return {"status": "success", "message": "Changes are correct and introduce no regressions."}

        finally:
            # 5. Clean up
            self._restore_files(repo_root, original_contents)
