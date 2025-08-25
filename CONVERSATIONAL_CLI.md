# The Conversational CLI and Self-Awareness

The Triangulum system's Command-Line Interface (CLI) is designed to be more than just a command executor; it is a conversational partner that provides a natural and intuitive interface to the powerful debugging engine. This document details how the CLI achieves its conversational capabilities and its self-awareness of the system's internal state.

## 1. Conversational Capabilities

The conversational nature of the CLI is achieved through a combination of natural language processing (NLP) powered by a Large Language Model (LLM) and a well-defined command structure.

*   **Natural Language Input:** The user can interact with the CLI using natural language commands like "fix the login bug" or "why is the test suite failing?". The `cli.py` module takes this input and uses the `api/llm_integrations.py` module to send the query to an LLM. The LLM's task is to parse this natural language command and map it to one of the system's internal commands or scripts.

*   **Intent-to-Command Mapping:** The LLM is prompted to act as an "intent parser". For example, the prompt might be: "You are an expert software engineer. The user said: 'fix the login bug'. Which of the following commands should be executed? `[run_bug_finder, run_tests, analyze_file, ...]`". The LLM's response is then used to invoke the appropriate function in the `cli.py` or a script from the `tooling/` directory.

*   **Interactive Dialog:** The CLI can engage in a multi-turn dialog with the user. If a user's request is ambiguous, the CLI, guided by the `agent_coordinator.py`, can ask clarifying questions. For example: "I found two failing tests related to 'login'. Which one should I start with?". This is implemented in `cli.py` by having a loop that waits for user input, sends it to the agent system, and then displays the agent's response (which could be a result or another question).

## 2. Self-Awareness of Internal State

The CLI's "self-awareness" refers to its ability to inspect and report on the state of the internal components of the Triangulum system (the "nodes"). This is achieved through the `monitoring/` and `core/` modules.

*   **System Monitor:** The `monitoring/system_monitor.py` module continuously collects metrics from the `core/triangulation_engine.py` (e.g., tick count, number of active agents, entropy levels). It pushes these metrics to a `MetricBus`.

*   **Status Command:** The `cli.py`'s `status` command subscribes to the `MetricBus` (or queries a snapshot of its latest state). When the user types `tri status`, the CLI formats and displays these metrics, providing a real-time view of the system's health and progress.

*   **Agent Awareness:** The `core/parallel_executor.py` maintains a list of all active bug-fixing "contexts", each with its own engine and agent coordinator. The `status` command can query the `parallel_executor` to get a list of active bugs and the state of their respective agent triangles (e.g., "Bug-42: VERIFYING").

*   **Dashboard Integration:** The `monitoring/dashboard_stub.py` provides a web-based view of the same metrics, offering a more graphical representation of the system's state. The CLI's `dashboard` command simply launches this FastAPI application.

## 3. The Command and Script Language

The true power of the CLI comes from the vast library of commands and scripts in the `tooling/` directory. The LLM-powered agents can be thought of as "reasoning engines" that decide which tools to use from this library.

*   **Combinatorial Power:** As we've discussed, the combination of these atomic commands and scripts creates a "language" with billions of possible "sentences" (sequences of commands). An agent is not limited to a few hard-coded actions; it can dynamically compose sequences of commands to tackle novel problems.

*   **Example Workflow:**
    1.  User: `tri fix the performance issue in the data processing pipeline`
    2.  `cli.py` sends this to the `PlannerAgent`.
    3.  The `PlannerAgent`, using an LLM, decides on a plan:
        *   `tooling/scope_filter.py`: Identify the relevant files in the data processing pipeline.
        *   `tooling/test_runner.py`: Run performance benchmarks to get a baseline.
        *   `tooling/file_stats.py`: Analyze the complexity and entropy of the relevant files.
        *   `AnalystAgent`: Propose a refactoring to optimize a high-entropy function.
        *   `tooling/repair.py`: Apply the refactoring.
        *   `tooling/test_runner.py`: Re-run benchmarks to verify the improvement.
    4.  The `agent_coordinator.py` executes this plan, calling the tools in sequence.
    5.  The `cli.py` reports the progress and final result to the user.

By combining a natural language interface with a powerful and extensible set of tools, the Triangulum CLI acts as the perfect bridge between human intent and the system's autonomous debugging capabilities.
