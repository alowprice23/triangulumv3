from pathlib import Path
import re
import click
from typing import Dict, Any

from agents.llm_config import LLMConfig
from agents.prompts import ANALYST_PROMPT
from tooling.patch_bundle import create_patch_bundle
from agents.memory import Memory

class Analyst:
    """
    The Analyst agent analyzes the bug report from the Observer, queries its
    memory for similar past fixes, and proposes a patch.
    """
    def __init__(self):
        self.llm_config = LLMConfig()
        self.llm_client = self.llm_config.get_client()
        self.memory = Memory()

    def _extract_code_from_llm(self, llm_response: str) -> str | None:
        """Extracts the code block from the LLM's markdown response."""
        match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def analyze_and_propose_patch(
        self,
        observer_report: Dict[str, Any],
        repo_root: Path
    ) -> Dict[str, Any]:
        """
        Analyzes the bug and generates a patch bundle and the full modified files.
        """
        if not observer_report.get("failing_tests"):
            return {"status": "no_op", "message": "No failing tests to analyze."}

        click.echo("Analyst: Analyzing failing tests and logs...")

        failing_test_path_str = observer_report["failing_tests"][0].split("::")[0]
        source_file_path_str = failing_test_path_str.replace("tests/test_", "")

        try:
            failing_test_content = (repo_root / failing_test_path_str).read_text()
            source_file_content = (repo_root / source_file_path_str).read_text()
        except FileNotFoundError as e:
            return {"status": "error", "message": f"Could not read file: {e}"}

        # Query memory for similar past fixes
        similar_fixes = self.memory.find_similar_fixes(
            error_log=observer_report["logs"],
            file_path=source_file_path_str
        )
        memory_context = "No similar fixes found in memory."
        if similar_fixes:
            memory_context = "Found the following similar past fixes:\n"
            for fix in similar_fixes:
                memory_context += f"- Patch for {fix['metadata']['source_file']}:\n{fix['metadata']['patch']}\n\n"

        prompt = ANALYST_PROMPT.format(
            failing_tests="\n".join(observer_report["failing_tests"]),
            logs=observer_report["logs"],
            memory_context=memory_context,
            file_contents=(
                f"--- {failing_test_path_str} ---\n{failing_test_content}\n\n"
                f"--- {source_file_path_str} ---\n{source_file_content}"
            )
        )

        click.echo("Analyst: Calling LLM to generate a fix...")
        llm_response = self.llm_client.get_completion(prompt, model=self.llm_config.model_name)

        if not llm_response:
            return {"status": "failed", "message": "LLM call failed or returned no response."}

        modified_code = self._extract_code_from_llm(llm_response)

        if not modified_code:
            return {"status": "failed", "message": "LLM failed to generate a patch from the response."}

        click.echo("Analyst: Creating patch bundle...")
        patch_bundle = create_patch_bundle(
            original_files={source_file_path_str: source_file_content},
            modified_files={source_file_path_str: modified_code}
        )

        return {
            "status": "success",
            "patch_bundle": patch_bundle,
            "modified_files": {source_file_path_str: modified_code},
            "llm_rationale": llm_response,
            "original_error_log": observer_report["logs"] # Pass this through for memory
        }
