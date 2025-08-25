# The Full Debugging Workflow: A Step-by-Step Example

This document illustrates the end-to-end workflow of the Triangulum system, from a high-level user request to a fully autonomous bug fix. This example demonstrates how the various components of the system work together to achieve a resolution.

## The Scenario

A user is experiencing a bug in their e-commerce application. When they try to apply a discount code to their shopping cart, the application crashes. The user initiates a debugging session with the Triangulum system.

## The Workflow

**Step 1: User Initiates Debugging via Conversational CLI**

The user opens their terminal and starts the Triangulum CLI:

```bash
tri debug my-ecommerce-app
```

The CLI responds:

> Hello! I'm the Triangulum debugging assistant. What can I help you with today?

User:

> When I apply a discount code, the app crashes.

**Step 2: Planning and Objective Setting**

The `cli.py` module sends the user's request to the `PlannerAgent`. The `PlannerAgent`, using the `goal/goal_loader.py` and an LLM, formulates a high-level plan:

1.  **Reproduce the bug:** Find a reliable way to trigger the crash.
2.  **Analyze the crash:** Determine the root cause of the crash.
3.  **Propose and apply a fix:** Generate and apply a patch to fix the bug.
4.  **Verify the fix:** Ensure the bug is fixed and no new issues have been introduced.

The `ObjectiveManager` in `goal/` tracks this plan.

**Step 3: The Observer Triangle (Bug Reproduction)**

The `agent_coordinator.py` assigns an **Observer** agent to the first task.

*   The Observer uses `tooling/scope_filter.py` to identify relevant files (e.g., `cart.py`, `discounts.py`, `api/checkout.py`).
*   It uses `tooling/test_runner.py` to run the existing test suite, looking for tests related to discounts or the shopping cart. It finds a failing test named `test_apply_invalid_discount_code`.
*   The Observer now has a deterministic way to reproduce the bug. It captures the failing test's output and the relevant parts of the application logs.
*   It uses `tooling/compress.py` to summarize the logs and test output into a concise report.

**Step 4: The Analyst Triangle (Root Cause Analysis and Patch Generation)**

The Observer hands off its report to an **Analyst** agent.

*   The Analyst examines the compressed logs and the code for `cart.py` and `discounts.py`. It uses `tooling/file_stats.py` to note that `discounts.py` has high entropy, suggesting it might be the source of the problem.
*   The Analyst, guided by an LLM, identifies a potential null pointer exception in `discounts.py`. A discount code that doesn't exist in the database returns `null`, but the code doesn't handle this case.
*   The Analyst uses its understanding of the P=NP solver to determine the most efficient way to patch the code. In this case, a simple null check is sufficient.
*   The Analyst generates a patch using `tooling/patch_bundle.py`.

**Step 5: The Verifier Triangle (Verification and No-Regression Check)**

The Analyst hands off the patch bundle to a **Verifier** agent.

*   The Verifier first applies the patch in a sandboxed environment using `tooling/sandbox_runner.py`.
*   It then runs the `test_apply_invalid_discount_code` test using `tooling/test_runner.py`. As per the deterministic protocol, the first run is designed to fail (to ensure the test is still valid). The Analyst makes a micro-adjustment (e.g., to a comment), and the second run passes.
*   The Verifier runs the *entire* test suite to ensure no regressions were introduced. All tests pass.
*   For an extra layer of safety, the Verifier uses `tooling/canary_runner.py` to deploy the patched code to a staging environment. It then uses `tooling/smoke_runner.py` to run a small set of critical end-to-end tests. All smoke tests pass.

**Step 6: Completion and Reporting**

The `ObjectiveManager` sees that all tasks in the plan are complete. The `core/verification_engine.py` confirms that all invariants were maintained and the system's entropy has decreased (the code is now less complex).

The `cli.py` reports back to the user:

> I've fixed the discount code crash. The issue was an unhandled case for non-existent codes. I've added a check to handle this. All tests, including a canary deployment, have passed. The fix is now live.

The user's problem is solved, and the system has autonomously navigated the entire debugging process, from understanding the user's request to deploying a verified fix. Throughout this process, the mathematical guarantees of the Triangulum system ensured that the process was efficient, predictable, and correct.
