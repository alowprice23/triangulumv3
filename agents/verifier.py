from pathlib import Path
import networkx as nx
from typing import Dict, Any, List, Optional

from tooling.test_runner import run_tests
from tooling.repair import RepairTool
from tooling.fuzz_runner import FuzzRunner

class Verifier:
    """
    The Verifier agent applies a change and runs tests to verify the fix
    and check for regressions. It can also use advanced tools like a
    ripple effect analyzer and a fuzz tester.
    """
    def __init__(self, dependency_graph: Optional[nx.DiGraph] = None):
        self.graph = dependency_graph

    def _get_original_file_contents(self, repo_root: Path, file_paths: List[str]) -> Dict[str, str]:
        """Reads and stores the original content of files to be changed."""
        contents = {}
        for file_path in file_paths:
            full_path = repo_root / file_path
            if full_path.exists():
                contents[file_path] = full_path.read_text()
            else:
                contents[file_path] = None
        return contents

    def _restore_files(self, repo_root: Path, original_contents: Dict[str, str]):
        """Restores files to their original content."""
        print("Verifier: Restoring original file contents...")
        for file_path, content in original_contents.items():
            full_path = repo_root / file_path
            if content is not None:
                full_path.write_text(content)
            elif full_path.exists():
                full_path.unlink()

    def verify_changes(
        self,
        analyst_report: Dict[str, Any],
        original_failing_tests: List[str],
        repo_root: Path
    ) -> Dict[str, Any]:
        modified_files = analyst_report.get("modified_files")
        if not modified_files:
            return {"status": "failed", "message": "No modified files found in analyst report."}

        files_to_change = list(modified_files.keys())
        original_contents = self._get_original_file_contents(repo_root, files_to_change)

        try:
            # 1. Confirm tests are still failing
            pre_patch_report = run_tests(repo_root, test_targets=original_failing_tests)
            if pre_patch_report.get("summary", {}).get("failed", 0) == 0:
                return {"status": "failed", "message": "Tests were not failing before applying changes."}

            # 2. Apply the changes
            for file_path, new_content in modified_files.items():
                (repo_root / file_path).write_text(new_content)

            # 2a. Analyze ripple effects
            if self.graph:
                repair_tool = RepairTool(self.graph)
                effects = repair_tool.analyze_ripple_effect(files_to_change)
                print(f"Verifier: Ripple effect analysis: {effects}")

            # 3. Confirm fix
            post_patch_report = run_tests(repo_root, test_targets=original_failing_tests)
            if post_patch_report.get("summary", {}).get("failed", 0) > 0:
                self._restore_files(repo_root, original_contents)
                return {"status": "failed", "message": "Tests are still failing after applying changes."}

            # 4. Check for regressions
            regression_report = run_tests(repo_root)
            if regression_report.get("summary", {}).get("failed", 0) > 0:
                self._restore_files(repo_root, original_contents)
                return {"status": "failed", "message": "Changes introduced regressions.", "details": regression_report}

            # 5. Run fuzz tests
            fuzz_runner = FuzzRunner(repo_root)
            for file_path in files_to_change:
                # A real implementation would need to know which function to fuzz
                fuzz_result = fuzz_runner.run_fuzz_test(file_path, "some_function")
                if fuzz_result.get("status") != "success":
                    self._restore_files(repo_root, original_contents)
                    return {"status": "failed", "message": "Fuzz testing found issues.", "details": fuzz_result}

            return {"status": "success", "message": "Changes are correct and introduce no regressions."}

        except Exception as e:
            self._restore_files(repo_root, original_contents)
            raise e
