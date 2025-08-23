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
from discovery.repo_scanner import RepoScanner
from discovery.ignore_rules import IgnoreRules
from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from entropy.estimator import estimate_initial_entropy, calculate_n_star
from runtime.human_hub import request_human_feedback

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

        # Initialize discovery components
        self.scanner = RepoScanner(ignore_rules=IgnoreRules(project_root=self.repo_root))

    def run_debugging_cycle(
        self,
        bug_description: str,
        initial_scope: list[str] = None # Scope is now optional
    ) -> Dict[str, Any]:
        """
        Runs the full O->A->V cycle to attempt to fix a bug,
        respecting the entropy budget N*.
        (README.md, "Inevitable Solution Formula")
        """
        print(f"Coordinator: Starting debugging cycle for: '{bug_description}'")

        # Perform a full repository scan to create a manifest
        print("Coordinator: Scanning repository...")
        repo_manifest = self.scanner.scan(self.repo_root)
        if not repo_manifest:
            return {"status": "aborted", "reason": "Repository is empty or all files are ignored."}

        # The scope is now the entire repository, not a manual subset
        scope = [item["path"] for item in repo_manifest]

        # Build symbol index and dependency graph
        print("Coordinator: Building symbol index and dependency graph...")
        symbol_index = build_symbol_index(self.repo_root, scope)
        dep_graph = build_dependency_graph(symbol_index, scope)

        final_result = {}
        state = "REPRO"
        observer_report = {}
        analyst_report = {}
        n = 0

        # Initialize entropy budget with placeholders
        H0 = 1.0
        g = 1.0
        N_star = 3 # Minimum attempts
        n = 0

        while n < N_star:
            print(f"\n--- Cycle {n+1}/{N_star}, State: {state} ---")

            if state == "REPRO":
                observer_report = self.observer.observe_bug(self.repo_root, scope)
                if observer_report.get("status") != "success" or not observer_report.get("failing_tests"):
                    final_result = {"status": "aborted", "reason": "Observer could not find a reproducible failure."}
                    state = "ESCALATE"
                else:
                    # With failing tests identified, we can estimate H0
                    H0 = estimate_initial_entropy(
                        observer_report["failing_tests"],
                        dep_graph,
                        self.repo_root
                    )
                    N_star = calculate_n_star(H0, g) # Recalculate with initial g
                    print(f"Coordinator: Dynamic Entropy Budget: H₀={H0:.2f}, g={g:.2f}, N*={N_star}")
                    state = "PATCH"

            elif state == "PATCH":
                analyst_report = self.analyst.analyze_and_propose_patch(
                    observer_report,
                    self.repo_root,
                    repo_manifest,
                    symbol_index
                )
                if analyst_report.get("status") != "success":
                    final_result = {"status": "failed", "reason": "Analyst could not generate a patch."}
                    state = "ESCALATE"
                else:
                    # With a patch proposed, we can estimate g and N*
                    g = analyst_report.get("g_estimation", 1.0)
                    N_star = calculate_n_star(H0, g)
                    print(f"Coordinator: Updated Entropy Budget: H₀={H0:.2f}, g={g:.2f}, N*={N_star}")
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

            if state == "ESCALATE":
                # If we've exhausted the budget, break the loop for real.
                if n >= N_star -1:
                    final_result = {"status": "failed", "reason": f"Exceeded entropy budget (N*={N_star}) even with human help."}
                    break

                human_hint = request_human_feedback({
                    "failing_tests": observer_report.get("failing_tests", []),
                    "logs": observer_report.get("logs", ""),
                    "reason": final_result.get("reason", "Unknown reason for escalation.")
                })
                observer_report["logs"] += f"\n--- Human Hint ---\n{human_hint}\n"
                state = "PATCH"
                # The loop continues to the next n

            elif state == "DONE":
                break

            n += 1

        if state != "DONE" and not final_result:
            final_result = {"status": "failed", "reason": f"Exceeded entropy budget (N*={N_star})."}

        # Log the final outcome for meta-tuning
        llm_config = {"model_name": self.analyst.llm_config.model_name}
        self.meta_tuner.tune_from_outcome(final_result, llm_config)

        return final_result
