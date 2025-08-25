import tempfile
import shutil
from pathlib import Path
import networkx as nx
from typing import Dict, Any, List, Optional
import subprocess

import tooling.test_runner
from tooling.repair import RepairTool
from tooling.patch_bundle import apply_patch_bundle
from security.scanner import scan_for_malicious_code
from adapters.base_adapter import LanguageAdapter
import runtime.metrics as metrics
import hashlib

class Verifier:
    """
    The Verifier agent applies a change and runs tests to verify the fix
    and check for regressions. All operations are performed in a temporary
    sandboxed copy of the repository.
    """
    def __init__(self, adapter: LanguageAdapter):
        self.adapter = adapter

    def verify_changes(
        self,
        analyst_report: Dict[str, Any],
        original_failing_tests: List[str],
        repo_root: Path,
        expect_fail: bool = False
    ) -> Dict[str, Any]:

        sandbox_dir = Path(tempfile.mkdtemp())

        try:
            # Create a sandboxed copy of the repository
            shutil.copytree(repo_root, sandbox_dir, dirs_exist_ok=True)

            patch_bundle = analyst_report.get("patch_bundle")
            if not patch_bundle:
                return {"status": "failed", "message": "No patch bundle found in analyst report."}

            # Security Scan: Check the patch for malicious code before applying
            patch_hash = hashlib.sha256(str(patch_bundle).encode()).hexdigest()[:8]
            for file_path, patch_content in patch_bundle.items():
                threat = scan_for_malicious_code(patch_content)
                if threat:
                    metrics.SECURITY_SCAN_FAILED.inc()
                    return {"status": "failed", "message": f"Security scan failed for {file_path}: {threat}"}

            # Apply the changes within the sandbox
            apply_results = apply_patch_bundle(patch_bundle, sandbox_dir)
            if apply_results.get("failed"):
                return {"status": "failed", "message": "Failed to apply patch bundle.", "details": apply_results["failed"]}

            # Run tests within the sandbox
            metrics.VERIFIER_CYCLES.labels(patch_hash=patch_hash).inc()

            # Use the adapter to get the correct test command
            test_command = self.adapter.get_test_command(original_failing_tests)
            report = tooling.test_runner.run_test_command(sandbox_dir, test_command)

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

            return {
                "status": status,
                "message": message,
                "details": report
            }

        finally:
            # Ensure the sandbox is always cleaned up
            shutil.rmtree(sandbox_dir)
