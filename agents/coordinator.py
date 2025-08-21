from pathlib import Path
from typing import Dict, Any

from agents.observer import Observer
from agents.analyst import Analyst
from agents.verifier import Verifier

class Coordinator:
    """
    The Coordinator manages the O->A->V (Observer, Analyst, Verifier)
    debugging cycle.
    """
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.observer = Observer()
        self.analyst = Analyst()
        self.verifier = Verifier()

    def run_debugging_cycle(
        self,
        bug_description: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Runs the full O->A->V cycle to attempt to fix a bug.

        Args:
            bug_description: A description of the bug to be fixed.
            max_retries: The maximum number of times to loop through the A->V cycle.

        Returns:
            A dictionary with the final result of the debugging process.
        """
        print(f"Coordinator: Starting debugging cycle for: '{bug_description}'")

        observer_report = self.observer.observe_bug(self.repo_root)
        if observer_report.get("status") != "success" or not observer_report.get("failing_tests"):
            print("Coordinator: Observer failed to find failing tests. Aborting.")
            return {"status": "aborted", "reason": "Observer could not find a reproducible failure."}

        original_failing_tests = observer_report["failing_tests"]

        for i in range(max_retries):
            print(f"\n--- Cycle {i+1}/{max_retries} ---")

            analyst_report = self.analyst.analyze_and_propose_patch(observer_report, self.repo_root)
            if analyst_report.get("status") != "success":
                print("Coordinator: Analyst failed to generate a patch. Aborting.")
                return {"status": "failed", "reason": "Analyst could not generate a patch."}

            # Call the renamed Verifier method
            verifier_report = self.verifier.verify_changes(
                analyst_report,
                original_failing_tests,
                self.repo_root
            )

            if verifier_report.get("status") == "success":
                print("Coordinator: Cycle successful! Bug fixed and verified.")
                return {
                    "status": "success",
                    "message": "Bug fixed successfully.",
                    "patch_bundle": analyst_report.get("patch_bundle"),
                    "modified_files": analyst_report.get("modified_files"),
                    "llm_rationale": analyst_report.get("llm_rationale")
                }
            else:
                details = verifier_report.get('details', 'No details provided.')
                print(f"Coordinator: Verifier failed. Reason: {verifier_report.get('message')}")
                print(f"Verifier Details: {details}")
                observer_report["logs"] += f"\n--- Attempt {i+1} Failed ---\n{verifier_report.get('message')}\nDetails: {details}"


        print(f"Coordinator: Failed to fix the bug after {max_retries} attempts.")
        return {"status": "failed", "reason": f"Exceeded max retries ({max_retries})."}
