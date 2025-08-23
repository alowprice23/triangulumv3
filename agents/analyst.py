from pathlib import Path
import re
import click
from typing import Dict, Any, List
import difflib

from agents.llm_config import LLMConfig
import networkx as nx
from agents.prompts import ANALYST_PROMPT
from tooling.patch_bundle import create_patch_bundle
from kb.patch_motif_library import PatchMotifLibrary
from discovery.code_graph import CodeGraph
from discovery.semantic_search import find_similar_symbols
from entropy.estimator import estimate_g_from_patch
import runtime.metrics as metrics

class Analyst:
    """
    The Analyst agent analyzes the bug report from the Observer, queries its
    memory for similar past fixes, and proposes a patch.
    (README.md, §2, "Three Core Agent Archetypes")
    """
    def __init__(self):
        self.llm_config = LLMConfig() # This will eventually be loaded from a global config
        self.llm_client = self.llm_config.get_client()
        self.kb = PatchMotifLibrary()

    def _extract_code_from_llm(self, llm_response: str) -> str | None:
        """Extracts the code block from the LLM's markdown response."""
        match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def analyze_and_propose_patch(
        self,
        observer_report: Dict[str, Any],
        repo_root: Path,
        code_graph: CodeGraph
    ) -> Dict[str, Any]:
        """
        Analyzes the bug, queries for context, and generates a patch.
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

        # Perform semantic search to find relevant code snippets
        click.echo("Analyst: Performing semantic search for relevant code...")
        error_log = observer_report.get("logs", "")
        similar_symbols = find_similar_symbols(code_graph, error_log)

        semantic_context = "No semantically similar code snippets found."
        if similar_symbols:
            semantic_context = "Found the following semantically similar code snippets:\n"
            for symbol, score in similar_symbols:
                semantic_context += f"--- Snippet from {symbol.name} (Similarity: {score:.2f}) ---\n"
                semantic_context += f"{symbol.source_code}\n\n"

        # Query the Knowledge Base for similar past fixes
        click.echo("Analyst: Querying Knowledge Base for similar fixes...")
        similar_motifs = self.kb.find_similar_motifs(
            error_log=observer_report["logs"],
            file_path=source_file_path_str
        )
        memory_context = "No similar fixes found in the Knowledge Base."
        if similar_motifs:
            memory_context = "Found the following similar past fixes in the Knowledge Base:\n"
            for motif in similar_motifs:
                patch_info = motif['metadata'].get('patch', 'Patch content not available.')
                source_file = motif['metadata'].get('source_file', 'Unknown source file.')
                memory_context += f"- Patch for {source_file}:\n{patch_info}\n\n"

        file_contents = (
            f"--- Failing Test: {failing_test_path_str} ---\n{failing_test_content}\n\n"
            f"--- Suspected Source File: {source_file_path_str} ---\n{source_file_content}\n\n"
        )

        prompt = ANALYST_PROMPT.format(
            failing_tests="\n".join(observer_report["failing_tests"]),
            logs=observer_report["logs"],
            memory_context=memory_context,
            semantic_context=semantic_context,
            strategic_advice=observer_report.get("strategic_advice", "No strategic advice available."),
            file_contents=file_contents
        )

        click.echo("Analyst: Calling LLM to generate a fix...")
        llm_response = self.llm_client.get_completion(prompt, model=self.llm_config.model_name)
        metrics.LLM_CALLS.labels(agent="Analyst", model=self.llm_config.model_name).inc()

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
        metrics.PATCHES_GENERATED.inc()

        # Estimate information gain (g) from the generated patch
        g = estimate_g_from_patch(
            original_content=source_file_content,
            patch_content=modified_code
        )
        click.echo(f"Analyst: Estimated information gain g = {g:.2f}")

        return {
            "status": "success",
            "patch_bundle": patch_bundle,
            "rationale": llm_response,
            "files_changed": [source_file_path_str],
            "original_error_log": observer_report["logs"],
            "g_estimation": g
        }
