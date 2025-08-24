# A-to-Z Guide for the Triangulum v3 System

## 1. Introduction: The Triangulum Philosophy

Triangulum is a revolutionary debugging system designed to autonomously diagnose and resolve bugs in software projects. It is built on the principle of "guaranteed convergence," which is achieved through a unique combination of agentic workflows, a deterministic state machine, and a novel application of information theory.

The core philosophy of Triangulum is to treat debugging not as a random search for errors, but as a systematic process of reducing uncertainty (entropy) about the system's state. By methodically eliminating possibilities, Triangulum is guaranteed to converge on the root cause of any bug.

## 2. System Architecture (The Ultimate File Map)

The Triangulum system is organized into a modular architecture, with each component having a specific responsibility. The following is the "ultimate file map" that defines the structure of the project:

*   **`adapters/`**: Language-specific adapters for parsing code and understanding different programming languages.
*   **`agents/`**: The core agentic components of the system:
    *   `observer.py`: The Observer agent, responsible for gathering information about the system's state.
    *   `analyst.py`: The Analyst agent, responsible for analyzing the gathered information and forming hypotheses.
    *   `verifier.py`: The Verifier agent, responsible for testing hypotheses and confirming bug fixes.
    *   `coordinator.py`: The Coordinator, which manages the lifecycle of the other agents.
    *   `meta_agent.py`: A meta-agent responsible for tuning the other agents' performance.
*   **`api/`**: The external API for interacting with the Triangulum system.
*   **`cli/`**: The command-line interface for the Triangulum system.
*   **`config/`**: Configuration files for the system.
*   **`discovery/`**: Modules for discovering information about the codebase, such as building a code graph and locating tests.
*   **`entropy/`**: The implementation of the entropy drain and P=NP solver, the mathematical core of Triangulum.
*   **`kb/`**: The knowledge base, which stores information about past bugs and their resolutions.
*   **`runtime/`**: The runtime environment for the Triangulum system, including the state machine, scheduler, and supervisor.
*   **`storage/`**: The storage backend for the system's state.
*   **`tooling/`**: A collection of tools that the agents can use to interact with the codebase, such as running tests and applying patches.
*   **`tests/`**: The test suite for the Triangulum system.

## 3. Setup and Configuration

To set up the Triangulum system, follow these steps:

1.  **Install dependencies:** `pip install -r requirements.txt`
2.  **Configure the environment:** Create a `.env` file in the root directory and specify the necessary environment variables, such as API keys for any external services.
3.  **Initialize the knowledge base:** Run the `kb_init` command to initialize the knowledge base.

## 4. The Conversational CLI

The primary way to interact with the Triangulum system is through its conversational CLI. The CLI allows you to:

*   **Start a debugging session:** `triangulum run --path /path/to/your/project`
*   **Monitor the system's progress:** `triangulum status`
*   **Interact with the agents:** The CLI will prompt you for input when the agents need guidance.

## 5. The Agentic Workflow

The Triangulum system uses a three-agent workflow to diagnose and fix bugs:

1.  **Observer:** The Observer agent gathers information about the system's state by running tests, inspecting logs, and analyzing the code.
2.  **Analyst:** The Analyst agent takes the information gathered by the Observer and forms hypotheses about the root cause of the bug.
3.  **Verifier:** The Verifier agent tests the Analyst's hypotheses by creating and running new tests. If a hypothesis is confirmed, the Verifier will attempt to generate a patch to fix the bug.

This cycle of observation, analysis, and verification continues until the bug is fixed.

## 6. Mathematical Guarantees (Entropy Drain and P=NP Solver)

The Triangulum system is built on a solid mathematical foundation that guarantees its convergence. This is achieved through two key concepts:

*   **Entropy Drain:** The system is designed to continuously reduce the entropy (uncertainty) of the system's state. This is done by systematically eliminating possibilities until only the root cause of the bug remains.
*   **P=NP Solver:** The Triangulum system includes a novel P=NP solver that is used to efficiently search the solution space for bug fixes. This allows the system to find solutions to complex bugs that would be intractable for traditional debugging methods.

## 7. Tooling

The Triangulum agents have access to a rich set of tools that allow them to interact with the codebase. These tools are located in the `tooling/` directory and include:

*   `test_runner.py`: A tool for running tests.
*   `patcher.py`: A tool for applying patches to the code.
*   `linter.py`: A tool for running a linter on the code.

## 8. Human-in-the-Loop (HITL) Review Hub

The Triangulum system is designed to be autonomous, but it also includes a human-in-the-loop review hub that allows human developers to monitor the system's progress and provide guidance when needed. The review hub can be accessed through a web interface.

## 9. Monitoring and Metrics

The Triangulum system exposes a variety of metrics that can be used to monitor its performance. These metrics are exposed through a Prometheus endpoint and can be visualized in a Grafana dashboard.

## 10. Example Debugging Session

Here is an example of a typical debugging session with Triangulum:

1.  **Start the session:** `triangulum run --path /path/to/your/project`
2.  **Observer gathers information:** The Observer runs the project's test suite and identifies a failing test.
3.  **Analyst forms a hypothesis:** The Analyst examines the failing test and the surrounding code and hypothesizes that the bug is caused by an off-by-one error in a loop.
4.  **Verifier tests the hypothesis:** The Verifier creates a new test that specifically targets the suspected off-by-one error. The test passes, confirming the hypothesis.
5.  **Verifier generates a patch:** The Verifier generates a patch to fix the off-by-one error.
6.  **Observer verifies the fix:** The Observer runs the entire test suite again with the patch applied. All tests pass.
7.  **Session ends:** The debugging session is complete, and the bug is fixed.

## 11. Troubleshooting

Here are some common issues and their solutions:

*   **Test runner is hanging:** This can be caused by a variety of issues, including a misconfigured environment or a bug in a specific test. Try running the tests manually to isolate the problem.
*   **Agents are not making progress:** If the agents seem to be stuck in a loop, it may be necessary to provide them with some guidance through the HITL review hub.

## 12. Roadmap to Completion

The following is a list of the pending tasks that need to be completed to finish the Triangulum v3 system:

*   **Implement the P=NP solver:** The core logic for the P=NP solver needs to be implemented in the `entropy/` directory.
*   **Complete the language adapters:** The adapters for all supported languages need to be completed.
*   **Implement the HITL review hub:** The web interface for the HITL review hub needs to be implemented.
*   **Create the Grafana dashboard:** A Grafana dashboard for monitoring the system's metrics needs to be created.
*   **Write more tests:** The test suite needs to be expanded to cover all of the system's functionality.
*   **Write the user manual:** A comprehensive user manual needs to be written.
*   **Beta test the system:** The system needs to be beta tested with a variety of real-world projects.
*   **Launch the system:** The system needs to be officially launched.
