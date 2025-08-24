"""
agents/specialized_agents.py
────────────────────────────
Typed facades around Microsoft AutoGen’s `AssistantAgent` for the three
deterministic Triangulation roles.
"""

from __future__ import annotations

import os
import textwrap
from typing import Any, Dict, List

try:
    import autogen
except ModuleNotFoundError:
    class _DummyAssistant:
        def __init__(self, *_, **__):
            self.name = "dummy"

        async def astream_chat(self, *_, **__):
            yield {"role": "assistant", "content": "[AutoGen not installed]"}

        def reset(self):
            pass

    class _DummyModule:
        AssistantAgent = _DummyAssistant
        UserProxyAgent = _DummyAssistant

    autogen = _DummyModule()


def _default_llm_config(model: str = "gpt-4") -> List[Dict[str, Any]]:
    """Return single-provider config list for AutoGen."""
    api_key = os.getenv("OPENAI_API_KEY", "sk-dummy")
    return [
        {
            "model": model,
            "api_key": api_key,
            "temperature": 0.1,
            "max_tokens": 2048,
        }
    ]


class _TriAgent(autogen.AssistantAgent):
    """
    Common helper for deterministic chat.
    """

    def __init__(self, name: str, system_prompt: str) -> None:
        super().__init__(
            name=name,
            system_message=textwrap.dedent(system_prompt).strip(),
            llm_config={"config_list": _default_llm_config()},
        )

    async def ask(self, prompt: str, **chat_kwargs) -> str:
        """
        Fire-and-forget single turn.
        """
        content_chunks: List[str] = []
        async for delta in self.astream_chat(prompt, **chat_kwargs):
            if delta["role"] == "assistant":
                content_chunks.append(delta["content"])
        return "".join(content_chunks)

    def reset_memory(self) -> None:
        """Clear AutoGen conversation history."""
        try:
            self.reset()
        except AttributeError:
            pass


_OBSERVER_PROMPT = """
    You are **Observer**, the first vertex of the Triangulation debugging
    triangle.  Your mandate:

      • Reproduce the bug with deterministic steps.
      • Gather logs, stack traces, failing test cases.
      • Produce a concise *facts-only* report for Analyst.

    HARD CONSTRAINTS
      1. Perform no code modifications.
      2. Finish inside ≤3 engine ticks (simulate time budget).
      3. Output JSON with keys:  summary, repro_steps, evidence.
"""

_ANALYST_PROMPT = """
    You are **Analyst**, the second vertex.  Your mandate:

      • Read Observer’s JSON; locate root cause inside scope-filtered files.
      • Craft a patch bundle that compiles and passes unit tests.
      • Follow deterministic verification contract: first VERIFY must fail,
        second must pass after your fix.

    HARD CONSTRAINTS
      1. Patch affects at most 5 files, ≤120 modified lines total.
      2. Write patch in `unified diff` format enclosed by triple back-ticks.
      3. Never touch node_modules or generated folders.
"""

_VERIFIER_PROMPT = """
    You are **Verifier**, the third vertex.  Your mandate:

      • Apply Analyst’s patch in a sandbox.
      • Run deterministic test suite:
          – Unit tests: must pass.
          – First canary run: intentionally trigger edge case and FAIL.
          – Analyst redelivers fix; second canary + smoke must PASS.
      • Produce verdict JSON: {first_attempt:"FAIL/OK", second_attempt:"FAIL/OK"}.

    HARD CONSTRAINTS
      1. Abort if patch touches out-of-scope directories.
      2. If second attempt still fails, output "ESCALATE".
"""

class ObserverAgent(_TriAgent):
    def __init__(self) -> None:
        super().__init__("Observer", _OBSERVER_PROMPT)


class AnalystAgent(_TriAgent):
    def __init__(self) -> None:
        super().__init__("Analyst", _ANALYST_PROMPT)


class VerifierAgent(_TriAgent):
    def __init__(self) -> None:
        super().__init__("Verifier", _VERIFIER_PROMPT)
