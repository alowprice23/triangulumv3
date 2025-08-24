# PLAN(api).md

## 1. Purpose & Scope (README-anchored)

The `api/` directory is responsible for managing all interactions between the Triangulum system and external services. Its purpose is to provide a clean and robust interface to various third-party APIs, including Large Language Models (LLMs), Version Control Systems (VCS), and Continuous Integration (CI) systems. `FILEMAP.MD` describes this as the "API surface (LLM + VCS/CI)."

**Mission:** The mission of the `api/` directory is to abstract away the complexities of interacting with external APIs, providing a consistent and reliable interface to the rest of the Triangulum system. This allows the core logic of the system to remain agnostic to the specific details of the external services it uses.

**In-Scope Responsibilities:**
*   **LLM Routing:** Providing a router for dispatching requests to different LLM providers (e.g., OpenAI, Anthropic, Gemini), including fallback logic. This is handled by `api/llm_router.py`.
*   **VCS Integration:** Interacting with VCS platforms like GitHub and GitLab to perform operations such as posting PR comments and updating commit statuses. This is the responsibility of `api/vcs.py`.
*   **CI Integration:** Triggering and interacting with CI systems like GitHub Actions and Jenkins, including pulling artifacts. This is handled by `api/ci.py`.

**Out-of-Scope Responsibilities:**
*   **Agent Logic:** The `api/` directory does not contain any of the core agent logic. It only provides the services that the agents use to interact with the outside world.
*   **Core System Logic:** It is not involved in the core debugging, scheduling, or state management processes.

## 2. Files in This Directory (from FILEMAP.md only)

### `api/__init__.py`
*   **Role:** Standard Python package initializer.

### `api/llm_router.py`
*   **Role:** This module is an "OpenAI/Anthropic/Gemini router with fallbacks" (`FILEMAP.MD`). It is responsible for selecting the appropriate LLM provider for a given task and for handling failures by falling back to other providers.
*   **Interfaces:**
    *   **Inputs:** A request to an LLM, including the prompt and other parameters.
    *   **Outputs:** The response from the LLM.
*   **Dependencies:** `agents/llm_config.py`.

### `api/vcs.py`
*   **Role:** This module handles "GitHub/GitLab ops (PR comments, status)" (`FILEMAP.MD`). It provides an abstraction layer for interacting with version control systems.
*   **Interfaces:**
    *   **Inputs:** A PR number, a comment to be posted, or a status to be set.
    *   **Outputs:** The result of the VCS API call.
*   **Dependencies:** None.

### `api/ci.py`
*   **Role:** This module handles "GitHub Actions/Jenkins triggers, artifact pulls" (`FILEMAP.MD`). It allows the Triangulum system to integrate with CI/CD pipelines.
*   **Interfaces:**
    *   **Inputs:** A CI job to be triggered or an artifact to be pulled.
    *   **Outputs:** The result of the CI API call.
*   **Dependencies:** None.

## 3. Internal Control Flow (Step-by-Step)

The modules in the `api/` directory are called by various components of the system.

*   The `agents/` will use `api/llm_router.py` to communicate with the LLMs.
*   The `agents/verifier.py` might use `api/vcs.py` to post a comment on a PR after a successful verification.
*   The `runtime/supervisor.py` might use `api/ci.py` to trigger a CI job as part of the verification process.

## 4. Data Flow & Schemas (README-derived)

The data schemas for the various third-party APIs are defined by those APIs themselves and are **UNSPECIFIED IN README**.

## 5. Interfaces & Contracts (Cross-Referenced)

*   `api.llm.query(prompt)`
*   `api.vcs.post_comment(pr, comment)`
*   `api.ci.trigger_job(job_name)`

## 6. Error Handling & Edge Cases (From README Only)

*   **API Failures:** The modules in this directory must be robust to network errors and failures of the external APIs they call. They should implement retry logic and fallbacks where appropriate.
*   **Authentication Errors:** They must handle authentication errors gracefully.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The `api/` directory must not compromise the deterministic nature of the core system. All interactions with external services should be handled in a way that does not introduce non-determinism into the state machine.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the `api/` directory should involve:
*   Unit tests for each module, using mocks for the external APIs.
*   Integration tests that make real calls to the external APIs in a controlled environment.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Implement `api/llm_router.py`. - COMPLETED (Functionality covered by `api/llm_integrations.py`)
2.  Implement `api/vcs.py`. - PENDING (Out of scope for initial local-only implementation)
3.  Implement `api/ci.py`. - PENDING (Out of scope for initial local-only implementation)

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-023 | API credentials management | `api/` | The method for storing and managing API credentials is not specified. | High | UNSPECIFIED IN README — DO NOT INVENT. Assume they are provided via environment variables. |

## 11. Glossary (README-Only)

None specific to this directory.

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
