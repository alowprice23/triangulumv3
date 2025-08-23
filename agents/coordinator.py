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
from agents.strategy_guide import StrategyGuide
from discovery.code_graph import CodeGraph, CodeGraphBuilder
from discovery.language_probe import probe_language
from adapters.router import get_language_adapter
from entropy.estimator import estimate_initial_entropy, calculate_n_star
from runtime.human_hub import request_human_feedback
from runtime.performance_logger import PerformanceLogger, PerformanceRecord
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

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
        # The Verifier can be initialized with a dependency graph to perform
        # more targeted regression testing in the future.
        self.verifier = None # Will be initialized once the language is known
        self.kb = PatchMotifLibrary()
        self.strategy_guide = StrategyGuide(log_path=Path("state/performance_log.jsonl"))
        self.performance_logger = PerformanceLogger(log_path=Path("state/performance_log.jsonl"))

    def run_debugging_cycle(
        self,
        bug_description: str,
        code_graph: CodeGraph | None = None
    ) -> Dict[str, Any]:
        """
        Runs the full O->A->V cycle to attempt to fix a bug,
        respecting the entropy budget N*.
        (README.md, "Inevitable Solution Formula")
        """
        start_time = time.time()
        logger.info(f"Coordinator: Starting debugging cycle for: '{bug_description}'")

        # 1. Build the Code Graph if it wasn't provided (for backward compatibility)
        if code_graph is None:
            logger.info("Coordinator: No pre-built code graph provided. Building now...")

            # 1a. Probe for language and get adapter
            all_files = [p for p in self.repo_root.rglob('*') if p.is_file()]
            language = probe_language(all_files)
            if language == "Unknown":
                return {"status": "aborted", "reason": "Could not determine the project's primary language."}
            logger.info(f"Detected language: {language}")
            adapter = get_language_adapter(language)

            # 1b. Build code graph using the detected language adapter
            code_graph_builder = CodeGraphBuilder(repo_root=self.repo_root, adapter=adapter)
            code_graph = code_graph_builder.build()

            if not code_graph.manifest:
                return {"status": "aborted", "reason": "Repository is empty or all files are ignored."}
            logger.info(f"Coordinator: Code graph built. Found {len(code_graph.manifest)} files.")
            self.verifier = Verifier(adapter)
        else:
            logger.info("Coordinator: Using pre-built code graph.")
            adapter = get_language_adapter(code_graph.language)
            self.verifier = Verifier(adapter)

        # The scope for agents is now derived from the code graph
        scope = [item.path for item in code_graph.manifest]

        final_result = {}
        state = "REPRO"
        observer_report = {}
        analyst_report = {}
        n = 0

        # Initialize entropy budget with placeholders
        H0 = 1.0
        g = 1.0
        N_star = 3 # Minimum attempts

        while n < N_star:
            logger.info(f"--- Cycle {n+1}/{N_star}, State: {state} ---")

            if state == "REPRO":
                observer_report = self.observer.observe_bug(self.repo_root, scope)
                if observer_report.get("status") != "success" or not observer_report.get("failing_tests"):
                    final_result = {"status": "aborted", "reason": "Observer could not find a reproducible failure."}
                    state = "ESCALATE"
                else:
                    # With failing tests identified, we can estimate H0
                    H0 = estimate_initial_entropy(
                        observer_report["failing_tests"],
                        code_graph.dependency_graph,
                        self.repo_root
                    )
                    N_star = calculate_n_star(H0, g) # Recalculate with initial g
                    logger.info(f"Coordinator: Dynamic Entropy Budget: H₀={H0:.2f}, g={g:.2f}, N*={N_star}")
                    state = "PATCH"

            elif state == "PATCH":
                # Get strategic advice before calling the analyst
                strategic_advice = self.strategy_guide.get_strategic_advice(observer_report.get("logs", ""))

                # The observer_report will be passed to the analyst.
                # We can add our new context to it.
                observer_report['strategic_advice'] = strategic_advice or "No relevant historical data found."

                analyst_report = self.analyst.analyze_and_propose_patch(
                    observer_report,
                    self.repo_root,
                    code_graph
                )
                if analyst_report.get("status") != "success":
                    final_result = {"status": "failed", "reason": "Analyst could not generate a patch."}
                    state = "ESCALATE"
                else:
                    # With a patch proposed, we can estimate g and N*
                    g = analyst_report.get("g_estimation", 1.0)
                    N_star = calculate_n_star(H0, g)
                    logger.info(f"Coordinator: Updated Entropy Budget: H₀={H0:.2f}, g={g:.2f}, N*={N_star}")
                    state = "VERIFY"

            elif state == "VERIFY":
                # First attempt (fail)
                logger.info("Coordinator: Verifier first attempt (expected to fail).")
                verifier_report_fail = self.verifier.verify_changes(
                    analyst_report, observer_report["failing_tests"], self.repo_root, expect_fail=True
                )

                # On the first attempt, we expect a 'fail' status because the bug is still present.
                # However, if it fails for a security reason, it's a terminal failure.
                if verifier_report_fail.get("status") == "failed" and "Security scan failed" in verifier_report_fail.get("message", ""):
                    final_result = verifier_report_fail
                    state = "DONE" # Treat as a terminal state to break the loop
                elif verifier_report_fail.get("status") != "fail":
                    final_result = {"status": "failed", "reason": "Verifier did not fail on the first attempt as expected."}
                    state = "ESCALATE"
                else:
                    # The test failed as expected, now try for a success
                    logger.info("Coordinator: Verifier second attempt (expected to succeed).")
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
                        logger.warning(f"Coordinator: Verifier failed on the second attempt. Reason: {verifier_report_succeed.get('message')}")
                        observer_report["logs"] += f"\n--- Attempt {n+1} Failed ---\n{verifier_report_succeed.get('message')}\nDetails: {details}"
                        final_result = verifier_report_succeed
                        state = "PATCH"

            if state == "ESCALATE":
                # If we've exhausted the budget, break the loop for real.
                if n >= N_star - 1:
                    final_result = {"status": "failed", "reason": f"Exceeded entropy budget (N*={N_star})."}
                    # One last chance for human intervention
                    human_context = {
                        "failing_tests": observer_report.get("failing_tests", []),
                        "logs": observer_report.get("logs", "No logs available."),
                        "last_failed_patch": analyst_report.get("patch_bundle", {}).get(
                            analyst_report.get("files_changed", [""])[0]
                        )
                    }
                    human_hint = request_human_feedback(human_context)
                    # This hint is for the user/supervisor, not for a retry
                    final_result["human_suggestion"] = human_hint
                    break

                state = "PATCH"

            elif state == "DONE":
                break

            n += 1

        if state != "DONE" and not final_result:
            final_result = {"status": "failed", "reason": f"Exceeded entropy budget (N*={N_star})."}

        # --- Performance Logging ---
        end_time = time.time()
        duration = end_time - start_time

        # Extract the single patch string for logging, if successful.
        successful_patch_str = None
        if final_result.get("status") == "success":
            patch_bundle = final_result.get("patch_bundle", {})
            if patch_bundle:
                # Assuming one file changed for simplicity in logging
                successful_patch_str = list(patch_bundle.values())[0]

        record = PerformanceRecord(
            session_id=str(start_time), # Using start time as a unique enough ID for now
            timestamp=datetime.fromtimestamp(end_time).isoformat(),
            final_status=final_result.get("status", "failed"),
            failure_reason=final_result.get("reason"),
            cycles_taken=n + 1,
            duration_seconds=duration,
            llm_provider=self.analyst.llm_config.provider,
            llm_model=self.analyst.llm_config.model_name,
            initial_entropy=H0,
            information_gain=g,
            human_suggestion_provided=bool(final_result.get("human_suggestion")),
            successful_patch=successful_patch_str
        )
        self.performance_logger.log_session(record)

        return final_result
