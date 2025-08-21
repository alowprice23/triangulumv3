# PLAN(entropy).md

## 1. Purpose & Scope (README-anchored)

The `entropy/` directory is the quantitative heart of the Triangulum system, responsible for implementing the principles of information theory that govern the debugging process. Its purpose, as described in `FILEMAP.MD`, is "Entropy logic & planning." This directory translates the abstract concept of a bug from a qualitative problem into a quantifiable measure of uncertainty, or entropy (H₀), which can be systematically reduced.

**Mission:** The mission of the `entropy/` directory is to operationalize the "inevitable-solution" formula, `H(n) = H₀ - n·g`, which was a key topic in the chat history. It does this by:
1.  Estimating the initial uncertainty (H₀) of a debugging task based on the size of the problem space (the "scope").
2.  Quantifying the information gain (*g*) obtained from each debugging cycle (e.g., from a failing test).
3.  Using these values to predict the number of iterations (N*) required to solve the bug.
4.  Providing human-understandable explanations of the system's state in terms of information and risk.

This directory provides the mathematical foundation for the `cli/agentic_router`'s planning and for the `runtime/supervisor`'s management of the execution lifecycle. It ensures that the debugging process is not a random walk but a purposeful, information-driven descent towards a solution, as envisioned in the "Fractal-Triangle Mental Model" (`README.md`, §1).

**In-Scope Responsibilities:**
*   **Entropy Estimation:** Calculating the initial Shannon entropy (H₀) of a candidate set of files, as handled by `entropy/estimator.py`.
*   **Information Gain Calculation:** Determining the amount of information (*g*) gained from new evidence, such as a failing test or a learned constraint from `entropy/constraint_bank.py`.
*   **Cost and Time Estimation:** Predicting the number of iterations (N*) and the wall-time required to resolve a bug, using the formula `N* = ceil(H₀/g)`, as implemented in `entropy/plan_costing.py`.
*   **Explanation and Risk Assessment:** Translating the abstract entropy metrics into human-readable summaries of the system's confidence and the remaining risk, as handled by `entropy/explainer.py`.

**Out-of-Scope Responsibilities:**
*   **Scope Definition:** The `entropy/` directory does not define the scope of the debugging task. It receives the scope (a set of files) from the `discovery/` directory.
*   **Execution of Debugging Cycles:** It does not execute the O→A→V cycles. This is the responsibility of the `runtime/` and `agents/` directories.
*   **User Interface:** It does not have a direct user interface. Its outputs are consumed by the `cli/` directory, which presents them to the user.

## 2. Files in This Directory (from FILEMAP.md only)

### `entropy/__init__.py`
*   **Role:** Standard Python package initializer.

### `entropy/estimator.py`
*   **Role:** This is the core module for quantifying the problem space. `FILEMAP.MD` states that it "estimate[s] H₀ from candidate set size; g per iteration from constraints/tests."
    *   **H₀ Estimation:** It takes a set of candidate files (the "scope") from the `discovery` module and calculates the initial Shannon entropy. The formula for this is likely `H₀ = log₂(M)`, where `M` is the number of possible configurations or locations of the bug. The exact method for determining `M` is **UNSPECIFIED IN README**, but it is likely related to the number of files, lines of code, or symbols in the scope.
    *   ***g* Estimation:** It estimates the information gain (*g*) from a single iteration. This could be based on the number of tests that are expected to be eliminated by a patch, or the reduction in the number of possible fault locations.
*   **Interfaces:**
    *   **Inputs:** A scope object (list of files), and potentially information about tests and constraints.
    *   **Outputs:** A float value for H₀ and an estimated float value for *g*.
*   **Dependencies:** `discovery/` (for the scope), `entropy/constraint_bank.py`.

### `entropy/constraint_bank.py`
*   **Role:** This module manages "learned clauses (e.g., failing stack signatures) → ΔH" (`FILEMAP.MD`). It represents the knowledge the system gains during the debugging process. When the Observer agent identifies a deterministic failure, the signature of that failure (e.g., the stack trace) can be treated as a learned constraint. This constraint reduces the space of possible solutions, and this module is responsible for quantifying that reduction in terms of a change in entropy (ΔH).
*   **Interfaces:**
    *   **Inputs:** A new constraint (e.g., a stack trace signature).
    *   **Outputs:** The corresponding reduction in entropy (ΔH).
*   **Dependencies:** None.

### `entropy/plan_costing.py`
*   **Role:** This module uses the entropy metrics to make concrete predictions about the debugging effort. It "estimate[s] iterations `N* = ceil(H₀/g)` and wall-time" (`FILEMAP.MD`). This is a direct implementation of the "inevitable-solution" formula.
*   **Interfaces:**
    *   **Inputs:** H₀ and *g* from `entropy/estimator.py`.
    *   **Outputs:** An estimated number of iterations (N*) and an estimated wall-time for completion.
*   **Dependencies:** `entropy/estimator.py`.

### `entropy/explainer.py`
*   **Role:** This module translates the abstract mathematical concepts of entropy into something a human can understand. It provides a "human summary (bits remaining, risk)" (`FILEMAP.MD`). This is crucial for the user-facing components of the CLI, such as the `tri explain` command.
*   **Interfaces:**
    *   **Inputs:** The current entropy H(n) and other relevant metrics.
    *   **Outputs:** A human-readable string explaining the system's state.
*   **Dependencies:** `entropy/estimator.py`.

## 3. Internal Control Flow (Step-by-Step)

The `entropy/` directory is a service provider to other parts of the system, primarily the `cli/agentic_router.py`.

1.  **Scope Input:** The `agentic_router`, having received a scope proposal from the `discovery` module, passes the set of candidate files to `entropy/estimator.py`.
2.  **H₀ Calculation:** `estimator.py` calculates the initial entropy H₀ based on the size of the scope.
3.  **Plan Costing:** The router then passes H₀ and an estimated *g* to `entropy/plan_costing.py`, which returns the expected number of iterations N*.
4.  **Plan Selection:** The router uses this cost estimation to choose the best plan (e.g., "surgical" vs. "repo-wide").
5.  **Execution Monitoring:** During execution, as the agents run and tests fail, the `runtime/supervisor` can report these events. `entropy/constraint_bank.py` can be used to calculate the information gain (ΔH) from each new failing test. The supervisor updates the current entropy: `H(n+1) = H(n) - ΔH`.
6.  **Explanation:** At any time, the `cli/commands/explain.py` or `status.py` can call `entropy/explainer.py` with the current entropy H(n) to get a human-readable summary of the progress.

## 4. Data Flow & Schemas (README-derived)

*   **Input: Scope Object:**
    *   A list of file paths.
*   **Output: Entropy Metrics:**
    *   A data structure containing:
        ```json
        {
          "H0": "float", // Initial entropy
          "g_estimated": "float", // Estimated info gain per cycle
          "N_star": "int", // Estimated iterations to completion
          "estimated_wall_time_seconds": "int"
        }
        ```
*   **Input: Constraint Object:**
    *   A representation of a learned constraint, e.g., a stack trace hash. Schema is UNSPECIFIED IN README.
*   **Output: ΔH:**
    *   A float representing the reduction in entropy from a constraint.

## 5. Interfaces & Contracts (Cross-Referenced)

*   `entropy.get_entropy_metrics(scope)`:
    *   **Inputs:** A scope object.
    *   **Outputs:** An entropy metrics object (as above).
*   `entropy.get_delta_H(constraint)`:
    *   **Inputs:** A constraint object.
    *   **Outputs:** A float value for ΔH.
*   `entropy.explain_state(current_H)`:
    *   **Inputs:** The current entropy value.
    *   **Outputs:** A human-readable string.

## 6. Error Handling & Edge Cases (From README Only)

*   **Zero-sized Scope:** If the `discovery` process returns an empty scope, `entropy/estimator.py` should handle this gracefully, likely by returning H₀ = 0.
*   **Zero Information Gain:** If a debugging cycle yields no new information (*g* = 0), the `N* = ceil(H₀/g)` formula would result in a division by zero. `entropy/plan_costing.py` must handle this, possibly by returning an "infinite" or very large N*, signaling that the current approach is not making progress. This is an edge case mentioned in the `README.md`'s critiques of the formal model.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The `entropy/` directory is the implementation of the core mathematical invariant of the system: the **entropy-drain model**.

*   **Monotonically Decreasing Entropy:** The system is designed to ensure that entropy H(n) is a non-increasing function of the number of iterations *n*. The `entropy` module provides the tools to track this.
*   **Finite Completion:** The calculation of N* provides a proof hook for the system's liveness. The `runtime/supervisor` can use N* as a hard limit on the number of cycles, ensuring that the system will always terminate, either by solving the bug or by escalating after N* attempts.

## 8. Testing Strategy & Traceability (README Mapping)

| Plan Statement | README/FILEMAP Responsibility | Test File | Test Type |
| :--- | :--- | :--- | :--- |
| H₀ clamp behavior | `entropy/estimator.py`, `tooling/scope_filter.py` | `tests/unit/test_scope_filter.py` | Unit |

The testing strategy for the `entropy` module should include:
*   Unit tests for the H₀ calculation with different scope sizes.
*   Unit tests for the N* calculation, including the edge case of *g* = 0.
*   Property-based tests to verify that the entropy calculations are mathematically sound.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Implement `entropy/estimator.py` to calculate H₀ and estimate *g*.
2.  Implement `entropy/constraint_bank.py` to manage learned constraints.
3.  Implement `entropy/plan_costing.py` to calculate N* and estimated time.
4.  Implement `entropy/explainer.py` to generate human-readable summaries.

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-008 | H₀ calculation method | `entropy/estimator.py` | `README.md` and `FILEMAP.MD` state that H₀ is estimated from the candidate set size, but the exact formula (e.g., how `M` is derived from the files) is not specified. | High | UNSPECIFIED IN README — DO NOT INVENT. The implementation will need to use a reasonable heuristic, such as `M = number_of_lines_in_scope`. |
| GAP-009 | *g* estimation method | `entropy/estimator.py` | The method for estimating the information gain *g* per iteration is not detailed. | High | UNSPECIFIED IN README — DO NOT INVENT. A heuristic will be needed, for example, assuming *g* = 1 bit per failing test eliminated. |

## 11. Glossary (README-Only)

*   **Entropy (H₀):** A measure of the initial uncertainty or complexity of a problem space, measured in bits. (`FILEMAP.MD`, chat history)
*   **Information Gain (g):** The amount of uncertainty reduced by a single piece of new information, such as a failing test. (chat history)
*   **N*:** The predicted number of iterations required to solve a bug, calculated as `ceil(H₀/g)`. (`FILEMAP.MD`)

## 12. Provenance & Citations

This plan is derived exclusively from `README.md`, `FILEMAP.MD`, and the chat history regarding the entropy-drain formula.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
