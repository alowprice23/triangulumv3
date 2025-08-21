from pathlib import Path
from typing import Dict, Any

from agents.observer import Observer
from agents.analyst import Analyst
from agents.verifier import Verifier
from agents.memory import Memory
from agents.meta_tuner import MetaTuner

class Coordinator:
    """
    The Coordinator manages the O->A->V (Observer, Analyst, Verifier)
    debugging cycle, and orchestrates memory and meta-learning.
    """
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.observer = Observer()
        self.analyst = Analyst()
        self.verifier = Verifier()
        self.memory = Memory()
        self.meta_tuner = MetaTuner()

    def run_debugging_cycle(
        self,
        bug_description: str,
        max_retries: int = 2 # Reduced for faster testing
    ) -> Dict[str, Any]:
        """
        Runs the full O->A->V cycle to attempt to fix a bug.
        """
        print(f"Coordinator: Starting debugging cycle for: '{bug_description}'")
        final_result = {}

        try:
            observer_report = self.observer.observe_bug(self.repo_root)
            if observer_report.get("status") != "success" or not observer_report.get("failing_tests"):
                final_result = {"status": "aborted", "reason": "Observer could not find a reproducible failure."}
                return final_result

            original_failing_tests = observer_report["failing_tests"]

            for i in range(max_retries):
                print(f"\n--- Cycle {i+1}/{max_retries} ---")

                analyst_report = self.analyst.analyze_and_propose_patch(observer_report, self.repo_root)
                if analyst_report.get("status") != "success":
                    final_result = {"status": "failed", "reason": "Analyst could not generate a patch."}
                    break

                verifier_report = self.verifier.verify_changes(
                    analyst_report, original_failing_tests, self.repo_root
                )

                if verifier_report.get("status") == "success":
                    final_result = {**verifier_report, **analyst_report} # Merge reports

                    # Add successful fix to memory
                    patch_bundle = analyst_report.get("patch_bundle", {})
                    for file_path, patch in patch_bundle.items():
                        self.memory.add_successful_fix(
                            patch_content=patch,
                            source_file=file_path,
                            error_log=analyst_report["original_error_log"]
                        )
                    break
                else:
                    details = verifier_report.get('details', 'No details provided.')
                    print(f"Coordinator: Verifier failed. Reason: {verifier_report.get('message')}")
                    observer_report["logs"] += f"\n--- Attempt {i+1} Failed ---\n{verifier_report.get('message')}\nDetails: {details}"
                    final_result = verifier_report

            if not final_result.get("status") == "success":
                 final_result = {"status": "failed", "reason": f"Exceeded max retries ({max_retries})."}

        finally:
            # Log the final outcome for meta-tuning
            llm_config = {"model_name": self.analyst.llm_config.model_name}
            self.meta_tuner.tune_from_outcome(final_result, llm_config)

        return final_result
