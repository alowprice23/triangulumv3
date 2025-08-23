from pathlib import Path
from typing import Dict, Any
from math import ceil, log2

from pathlib import Path
from typing import Dict, Any
from math import ceil, log2

from agents.observer import Observer
from agents.analyst import Analyst
from agents.verifier import Verifier
from kb.patch_motif_library import PatchMotifLibrary
from agents.meta_tuner import MetaTuner

class Coordinator:
    """
    The Coordinator manages the O->A->V (Observer, Analyst, Verifier)
    debugging cycle, and orchestrates memory and meta-learning, all
    within the deterministic, entropy-driven framework specified in
    the README.md.
    """
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.observer = Observer()
        self.analyst = Analyst()
        self.verifier = Verifier()
        self.kb = PatchMotifLibrary()
        self.meta_tuner = MetaTuner()

    def run_debugging_cycle(
        self,
        bug_description: str,
        initial_scope: list[str]
    ) -> Dict[str, Any]:
        """
        Runs the full O->A->V cycle to attempt to fix a bug,
        respecting the entropy budget N*.
        (README.md, "Inevitable Solution Formula")
        """
        print(f"Coordinator: Starting debugging cycle for: '{bug_description}'")
        final_result = {}

        # Entropy budget initialization (README.md, "Inevitable Solution Formula")
        H0 = log2(len(initial_scope)) if initial_scope and len(initial_scope) > 1 else 1.0
        g = 1.0
        # N_star must be at least 3 to allow for the "fail first, then succeed" cycle.
        N_star = max(3, ceil(H0 / g) if g > 0 else 1)

        print(f"Coordinator: Entropy budget: H₀={H0:.2f}, g={g:.2f}, N*={N_star}")

        state = "REPRO"
        observer_report = {}
        analyst_report = {}
        n = 0

        while n < N_star:
            print(f"\n--- Cycle {n+1}/{N_star}, State: {state} ---")

            if state == "REPRO":
                observer_report = self.observer.observe_bug(self.repo_root, initial_scope)
                if observer_report.get("status") != "success" or not observer_report.get("failing_tests"):
                    final_result = {"status": "aborted", "reason": "Observer could not find a reproducible failure."}
                    state = "ESCALATE"
                else:
                    state = "PATCH"

            elif state == "PATCH":
                analyst_report = self.analyst.analyze_and_propose_patch(observer_report, self.repo_root)
                if analyst_report.get("status") != "success":
                    final_result = {"status": "failed", "reason": "Analyst could not generate a patch."}
                    state = "ESCALATE"
                else:
                    state = "VERIFY"

            elif state == "VERIFY":
                # First attempt (fail)
                print("Coordinator: Verifier first attempt (expected to fail).")
                verifier_report_fail = self.verifier.verify_changes(
                    analyst_report, observer_report["failing_tests"], self.repo_root, expect_fail=True
                )

                if verifier_report_fail.get("status") != "fail":
                    final_result = {"status": "failed", "reason": "Verifier did not fail on the first attempt as expected."}
                    state = "ESCALATE"
                else:
                    # Second attempt (succeed)
                    print("Coordinator: Verifier second attempt (expected to succeed).")
                    verifier_report_succeed = self.verifier.verify_changes(
                        analyst_report, observer_report["failing_tests"], self.repo_root
                    )

                    if verifier_report_succeed.get("status") == "success":
                        final_result = {**verifier_report_succeed, **analyst_report}
                        patch_bundle = analyst_report.get("patch_bundle", {})
                        # Save the successful fix to the Knowledge Base
                        for file_path, patch in patch_bundle.items():
                            self.kb.add_motif(
                                patch_content=patch,
                                source_file=file_path,
                                error_log=analyst_report.get("original_error_log", "")
                            )
                        state = "DONE"
                    else:
                        details = verifier_report_succeed.get('details', 'No details provided.')
                        print(f"Coordinator: Verifier failed on the second attempt. Reason: {verifier_report_succeed.get('message')}")
                        observer_report["logs"] += f"\n--- Attempt {n+1} Failed ---\n{verifier_report_succeed.get('message')}\nDetails: {details}"
                        final_result = verifier_report_succeed
                        state = "PATCH"

            if state == "DONE" or state == "ESCALATE":
                break

            n += 1

        if state != "DONE" and not final_result:
            final_result = {"status": "failed", "reason": f"Exceeded entropy budget (N*={N_star}). Escalating."}

        # Log the final outcome for meta-tuning
        llm_config = {"model_name": self.analyst.llm_config.model_name}
        self.meta_tuner.tune_from_outcome(final_result, llm_config)

        return final_result
