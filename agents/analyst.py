from pathlib import Path
import re
from typing import Dict, Any

from agents.llm_config import LLMConfig
from agents.prompts import ANALYST_PROMPT
from tooling.patch_bundle import create_patch_bundle

class Analyst:
    """
    The Analyst agent analyzes the bug report from the Observer and
    proposes a patch.
    """
    def __init__(self):
        self.llm_config = LLMConfig()
        self.llm_client = self.llm_config.get_client()

    def _extract_code_from_llm(self, llm_response: str) -> str | None:
        """Extracts the code block from the LLM's markdown response."""
        match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1) # Keep trailing newline if present
        return None

    def analyze_and_propose_patch(
        self,
        observer_report: Dict[str, Any],
        repo_root: Path
    ) -> Dict[str, Any]:
        """
        Analyzes the bug and generates a patch bundle and the full modified files.

        Args:
            observer_report: The report from the Observer agent.
            repo_root: The root path of the repository.

        Returns:
            A dictionary containing the patch bundle and modified file contents.
        """
        if not observer_report.get("failing_tests"):
            return {"status": "no_op", "message": "No failing tests to analyze."}

        print("Analyst: Analyzing failing tests and logs...")

        failing_test_path_str = observer_report["failing_tests"][0].split("::")[0]
        source_file_path_str = failing_test_path_str.replace("tests/test_", "")

        try:
            failing_test_content = (repo_root / failing_test_path_str).read_text()
            source_file_content = (repo_root / source_file_path_str).read_text()
        except FileNotFoundError as e:
            return {"status": "error", "message": f"Could not read file: {e}"}

        context = ANALYST_PROMPT.format(
            failing_tests="\n".join(observer_report["failing_tests"]),
            logs=observer_report["logs"],
            file_contents=(
                f"--- {failing_test_path_str} ---\n{failing_test_content}\n\n"
                f"--- {source_file_path_str} ---\n{source_file_content}"
            )
        )

        print("Analyst: Calling LLM to generate a fix...")
        llm_response = self.llm_client("propose_fix", context)

        modified_code = self._extract_code_from_llm(llm_response)

        if not modified_code:
            print("Analyst: LLM did not provide a valid code fix.")
            return {"status": "failed", "message": "LLM failed to generate a patch."}

        print("Analyst: Creating patch bundle...")
        patch_bundle = create_patch_bundle(
            original_files={source_file_path_str: source_file_content},
            modified_files={source_file_path_str: modified_code}
        )

        return {
            "status": "success",
            "patch_bundle": patch_bundle,
            "modified_files": {source_file_path_str: modified_code},
            "llm_rationale": llm_response
        }
