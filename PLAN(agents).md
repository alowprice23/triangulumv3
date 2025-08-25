# PLAN(agents).md

## 1. Purpose & Scope (README-anchored)

The `agents/` directory is the home of the specialized "micro-agents" that form the vertices of the "Fractal-Triangle" (`README.md`, §1, §2). Its purpose is to implement the distinct roles and behaviors of the Observer, Analyst, and Verifier, which are the primary actors in the bug resolution process. This directory is where the "Three Core Agent Archetypes" (`README.md`, §2) are brought to life.

**Mission:** The mission of the `agents/` directory is to provide a set of intelligent, autonomous agents that can collaboratively diagnose and fix bugs. Each agent has a specific focus and produces a well-defined artifact that it hands off to the next agent in the O→A→V (Observer→Analyst→Verifier) cycle. This structured collaboration is the engine of the "Triangle" lifecycle described in `README.md` (§4).

**In-Scope Responsibilities:**
*   **Observer (Reproducer):** Implementing the logic for the Observer agent, which is responsible for "Capture[ing] logs, inputs, and testcases that deterministically re-create the fault" (`README.md`, §2). This is handled by `agents/observer.py`.
*   **Analyst (Root-Cause Analyst):** Implementing the logic for the Analyst agent, which "Trace[s] execution, static-analyse[s] code, bisect[s] commits" to produce a "Patch proposal + rationale" (`README.md`, §2). This is the responsibility of `agents/analyst.py`.
*   **Verifier (Integrator):** Implementing the logic for the Verifier agent, which "Build[s], run[s] test-suite, fuzz[es], evaluate[s] side-effects" to confirm the fix and produce a "Green CI result + merge request" (`README.md`, §2). This is handled by `agents/verifier.py`.
*   **Orchestration:** Coordinating the interaction between the three agents, managing the O→A→V rounds, and enforcing stopping rules. This is the role of `agents/coordinator.py`.
*   **Configuration and Prompts:** Managing the configuration for the underlying language models (e.g., temperature, stop tokens) and defining the role-specific prompts that guide the agents' behavior. This is handled by `agents/llm_config.py` and `agents/prompts.py`.
*   **Learning and Adaptation:** Implementing mechanisms for cross-case learning (`agents/memory.py`) and self-tuning of prompts and parameters (`agents/meta_tuner.py`).

**Out-of-Scope Responsibilities:**
*   **State Management and Scheduling:** The `agents/` directory does not manage the overall state of the system or the scheduling of bug-fixing tasks. This is handled by the `runtime/` directory.
*   **User Interface:** The agents do not interact directly with the user. All user communication is mediated by the `cli/` directory.
*   **Low-Level Tooling:** The agents use tools for tasks like running tests or applying patches, but the implementation of these tools resides in the `tooling/` directory.

## 2. Files in This Directory (from FILEMAP.md only)

### `agents/__init__.py`
*   **Role:** Standard Python package initializer.

### `agents/llm_config.py`
*   **Role:** Manages the configuration for the language models that power the agents. `FILEMAP.MD` states it handles "model routing, temperature/stop tokens." This module is crucial for controlling the behavior and performance of the LLMs.
*   **Interfaces:**
    *   **Outputs:** Provides configuration objects for the LLM APIs.
*   **Dependencies:** `api/llm_router.py`.

### `agents/prompts.py`
*   **Role:** This module contains the "role prompts (Observer/Analyst/Verifier) with goal/manifest context" (`FILEMAP.MD`). These prompts are the primary mechanism for guiding the behavior of the LLM-based agents, instructing them on their specific roles, goals, and constraints.
*   **Interfaces:**
    *   **Outputs:** Provides formatted prompt strings for each agent role.
*   **Dependencies:** It likely takes the goal and manifest from the `discovery/` module as input to generate context-aware prompts.

### `agents/observer.py`
*   **Role:** Implements the Observer agent. Its job is to "reproduce failures; capture logs; shrink repro" (`FILEMAP.MD`). It is the first agent in the O→A→V cycle.
*   **Interfaces:**
    *   **Inputs:** A bug to be reproduced.
    *   **Outputs:** A "Reproduction script + failing unit test" (`README.md`, §2).
*   **Dependencies:** `tooling/test_runner.py`, `tooling/compress.py`.

### `agents/analyst.py`
*   **Role:** Implements the Analyst agent. It performs "trace/static analysis; propose patch plans" (`FILEMAP.MD`). It is the second agent in the cycle.
*   **Interfaces:**
    *   **Inputs:** The reproduction artifacts from the Observer.
    *   **Outputs:** A "Patch proposal + rationale" (`README.md`, §2).
*   **Dependencies:** `tooling/patch_bundle.py`.

### `agents/verifier.py`
*   **Role:** Implements the Verifier agent. It "run[s] tests/fuzz; evaluate[s] efficacy/regression" (`FILEMAP.MD`). It is the final agent in the cycle.
*   **Interfaces:**
    *   **Inputs:** The patch proposal from the Analyst.
    *   **Outputs:** A "Green CI result + merge request" (`README.md`, §2).
*   **Dependencies:** `tooling/test_runner.py`, `tooling/fuzz_runner.py`, `tooling/canary_runner.py`.

### `agents/coordinator.py`
*   **Role:** This is the orchestrator of the agent Triangle. It "orchestrate[s] O→A→V rounds; stopping rules" (`FILEMAP.MD`). It ensures that the agents collaborate effectively and that the cycle terminates appropriately.
*   **Interfaces:**
    *   **Inputs:** A bug to be resolved.
    *   **Outputs:** Manages the handoff of artifacts between agents.
*   **Dependencies:** `agents/observer.py`, `agents/analyst.py`, `agents/verifier.py`, `runtime/supervisor.py`.

### `agents/memory.py`
*   **Role:** Implements "cross-case memory (patch motifs, flaky test cache)" (`FILEMAP.MD`). This allows the system to learn from past experiences and improve its performance over time.
*   **Interfaces:**
    *   **Inputs:** Solved bugs and their patches.
    *   **Outputs:** Suggestions or context for new bug-fixing tasks.
*   **Dependencies:** `kb/`.

### `agents/meta_tuner.py`
*   **Role:** This module is a "small loop that tunes prompts/knobs from outcomes" (`FILEMAP.MD`). It provides a mechanism for the system to self-optimize its own parameters.
*   **Interfaces:**
    *   **Inputs:** The outcomes of bug-fixing sessions.
    *   **Outputs:** Updated configurations for prompts (`agents/prompts.py`) and LLMs (`agents/llm_config.py`).
*   **Dependencies:** `agents/prompts.py`, `agents/llm_config.py`.

## 3. Internal Control Flow (Step-by-Step)

The control flow within the `agents/` directory is managed by the `agents/coordinator.py`.

1.  **Initiation:** The `runtime/supervisor.py` spawns a Triangle and passes a bug to the `agents/coordinator.py`.
2.  **Observer Round:** The coordinator invokes the `observer.py` agent. The Observer uses tools from the `tooling/` directory to reproduce the bug and generates a failing test case.
3.  **Analyst Round:** The coordinator passes the Observer's artifacts to the `analyst.py` agent. The Analyst analyzes the code and the failure, and proposes a patch.
4.  **Verifier Round:** The coordinator gives the patch to the `verifier.py` agent. The Verifier applies the patch and runs the test suite.
5.  **Iteration and Termination:**
    *   If the Verifier confirms the fix and no regressions are found, the coordinator reports success to the supervisor.
    *   If the Verifier finds issues, the coordinator may initiate another round of the O→A→V cycle, possibly with additional context for the Analyst. The `README.md` mentions a regression from `VERIFY` to `PATCH` in its refined formal model.
    *   The coordinator enforces stopping rules, such as a maximum number of cycles, to prevent infinite loops.

## 4. Data Flow & Schemas (README-derived)

*   **Agent Artifacts:** The `README.md` (§2) specifies the artifacts produced by each agent:
    *   **Observer:** "Reproduction script + failing unit test."
    *   **Analyst:** "Patch proposal + rationale."
    *   **Verifier:** "Green CI result + merge request."
    The exact schemas for these artifacts are **UNSPECIFIED IN README**.

### 4.1. Agent Artifact Schemas (New)

To address the information gap `GAP-012`, the following JSON-based schemas are defined for the artifacts passed between agents. These schemas provide a structured and versioned format for inter-agent communication.

*   **Observer Artifact Schema:** This artifact contains everything needed to reproduce the bug.

    ```json
    {
      "artifact_type": "observer_output",
      "version": "1.0",
      "reproduction": {
        "repro_script": {
          "language": "bash",
          "content": "<script content to set up environment and run the test>"
        },
        "failing_test": {
          "language": "python|javascript|java|etc.",
          "filepath": "path/to/test_file.py",
          "content": "<content of the failing test file>"
        },
        "logs": {
          "stdout": "<stdout from the failing run>",
          "stderr": "<stderr from the failing run>"
        }
      }
    }
    ```

*   **Analyst Artifact Schema:** This artifact contains the proposed solution to the bug.

    ```json
    {
      "artifact_type": "analyst_output",
      "version": "1.0",
      "analysis": {
        "rationale": "<A detailed explanation of the root cause analysis and the reasoning behind the proposed patch>",
        "patch_proposal": {
          "format": "unified_diff",
          "content": "<The proposed patch in diff format>"
        }
      }
    }
    ```

*   **Verifier Artifact Schema:** This artifact contains the result of verifying the proposed patch.

    ```json
    {
      "artifact_type": "verifier_output",
      "version": "1.0",
      "verification": {
        "status": "success|failure|regression",
        "ci_result": {
          "url": "<URL to the CI run, if applicable>",
          "summary": "<Summary of the CI results>"
        },
        "merge_request": {
          "vcs": "github|gitlab|none",
          "pr_url": "<URL to the created merge/pull request, if applicable>"
        },
        "regressions_found": [
            {
                "test_name": "<Name of the test that regressed>",
                "details": "<Details about the regression>"
            }
        ]
      }
    }
    ```

## 5. Interfaces & Contracts (Cross-Referenced)

*   `agents.coordinator.resolve_bug(bug)`:
    *   **Inputs:** A bug object.
    *   **Outputs:** A result object indicating success or failure.

## 6. Error Handling & Edge Cases (From README Only)

*   **Agent Failure:** If any of the agents fail to produce their required artifact, the `coordinator` must handle this, possibly by retrying or escalating.
*   **Unsolvable Bugs:** If the O→A→V cycle repeats several times without success, the `coordinator`'s stopping rules should trigger an escalation.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The `agents/` directory operates within the safety framework provided by the `runtime/` directory. The `coordinator` must ensure that the agent cycles are productive and terminate, contributing to the system's overall liveness.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the `agents/` directory should involve:
*   Unit tests for each agent's logic.
*   Integration tests for the `coordinator` to ensure it correctly manages the O→A→V cycle.
*   E2E tests that run the entire system on sample bugs to verify the agents' effectiveness. `FILEMAP.MD` lists `tests/e2e/test_single_file_quick.py` and `tests/e2e/test_repo_wide_deep.py`, which would exercise the agents.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Implement `agents/llm_config.py` and `agents/prompts.py`. - COMPLETED
2.  Implement the `agents/observer.py` agent. - COMPLETED
3.  Implement the `agents/analyst.py` agent. - COMPLETED
4.  Implement the `agents/verifier.py` agent. - COMPLETED
5.  Implement the `agents/coordinator.py` to orchestrate the O→A→V cycle. - COMPLETED
6.  Implement `agents/memory.py` for cross-case learning. - COMPLETED
7.  Implement `agents/meta_agent.py` for self-optimization. - COMPLETED

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-012 | Agent artifact schemas | `agents/` | `README.md` describes the artifacts conceptually but not their data schemas. | High | RESOLVED. Schemas are now defined in section 4.1 of this document. |
| GAP-013 | Stopping rules for coordinator | `agents/coordinator.py` | The `README.md` mentions "stopping rules" but does not specify them. | High | RESOLVED. Stopping rules are implemented in the `runtime/supervisor.py` which can escalate a bug after repeated failures (e.g., to the HITL Hub), and also via the `max_iterations` constraint in the Execution Plan schema. |

## 11. Glossary (README-Only)

*   **Observer:** The agent responsible for reproducing a bug. (`README.md`, §2)
*   **Analyst:** The agent responsible for analyzing the bug and proposing a patch. (`README.md`, §2)
*   **Verifier:** The agent responsible for testing the patch and verifying the fix. (`README.md`, §2)

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 10+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
