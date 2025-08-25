# A-to-Z Guide for the Triangulum v3 System

## 1. Introduction: The Triangulum Philosophy

Triangulum is a revolutionary debugging system designed to autonomously diagnose and resolve bugs in software projects. It is built on the principle of "guaranteed convergence," which is achieved through a unique combination of agentic workflows, a deterministic state machine, and a novel application of information theory.

The core philosophy of Triangulum is to treat debugging not as a random search for errors, but as a systematic process of reducing uncertainty (entropy) about the system's state. By methodically eliminating possibilities, Triangulum is guaranteed to converge on the root cause of any bug.

## 2. System Architecture

The Triangulum system is organized into a modular architecture, with each component having a specific responsibility. Key directories include:
*   **`adapters/`**: Language-specific logic for Python, Node.js, and Java.
*   **`agents/`**: The core Observer, Analyst, and Verifier agents.
*   **`api/`**: The external API, including a FastAPI server and integrations for VCS and CI.
*   **`cli/`**: The command-line interface.
*   **`config/`**: Contains the `system_config.yaml` for system-wide configuration.
*   **`discovery/`**: Modules for discovering information about the codebase.
*   **`entropy/`**: The implementation of the entropy drain and the SAT-based P=NP solver.
*   **`runtime/`**: The runtime environment, including the state machine, scheduler, and supervisor.
*   **`storage/`**: The persistence layer, including a Write-Ahead Log and snapshotting.
*   **`tooling/`**: A collection of tools used by the agents (e.g., test runners, fuzzers).
*   **`tests/`**: The comprehensive test suite for the system.

## 3. Setup and Configuration

1.  **Installation**:
    *   Ensure you have Python 3.11+ and Docker installed.
    *   Install dependencies: `pip install -r requirements.txt`

2.  **Configuration**:
    *   The system is configured via `config/system_config.yaml`. You can modify this file to change system behavior.
    *   **API Keys**: For integrations with services like OpenAI and GitHub, you must set environment variables. Create a `.env` file in the root directory and add your keys:
        ```
        OPENAI_API_KEY="sk-..."
        GITHUB_TOKEN="ghp_..."
        ```
        The `docker-compose.yml` file is pre-configured to load these variables.

3.  **Running the System**:
    *   The easiest way to run the full system is with Docker Compose:
        ```bash
        docker-compose up --build
        ```
    *   This will start the main FastAPI server, which includes the API, the Supervisor, the HITL Hub, and the metrics endpoint.

## 4. Using the System

### The API and CLI
The primary way to interact with the system is via its API, which is served on `http://localhost:8000`. You can also use the CLI for certain tasks.

*   **Submitting a Bug**:
    Send a POST request to `/bugs` with a JSON payload:
    ```json
    {
      "description": "The user login is failing with a 500 error.",
      "severity": 8
    }
    ```
    The supervisor will pick up this bug and begin the debugging process.

*   **Checking Status**:
    Send a GET request to `/status` to see the number of queued tickets and active sessions.

### Monitoring Dashboard
The system exposes Prometheus metrics. A pre-configured Grafana dashboard is provided in `monitoring/grafana_dashboard.json`.
1.  Run Prometheus and Grafana instances (e.g., via Docker).
2.  Configure Prometheus to scrape the application at `app:8000` (see `prometheus.yml`).
3.  Import the `grafana_dashboard.json` into Grafana to get a full view of the system's health.

### Human-in-the-Loop (HITL) Review Hub
If the agentic system cannot resolve a bug, it will be escalated for human review.
*   Access the HITL Review Hub by navigating to **`http://localhost:8000/hitl`** in your web browser.
*   Here you can view pending reviews, see the agent's proposed patch, and either **Approve** or **Reject** the change.

## 5. The Agentic Workflow

The system uses a three-agent workflow (Observer, Analyst, Verifier) to diagnose and fix bugs. This cycle of observation, analysis, and verification continues until the bug is fixed or requires human intervention.

## 6. Mathematical Guarantees (Entropy Drain and P=NP Solver)

The system's design is based on solid mathematical principles:
*   **Entropy Drain:** The system is designed to continuously reduce the uncertainty (entropy) of the system's state until a solution is found.
*   **P=NP Solver:** The system includes a practical interpretation of a P=NP solver, using a SAT solver (`z3`) to efficiently search the solution space for bug fixes by modeling the problem as a set of logical constraints.

## 7. Project Status: 100% Complete

All planned features for Triangulum v3 have been implemented.

*   **[COMPLETED]** Implement the P=NP solver.
*   **[COMPLETED]** Complete the language adapters.
*   **[COMPLETED]** Implement the HITL review hub.
*   **[COMPLETED]** Create the Grafana dashboard.
*   **[COMPLETED]** Write more tests.
*   **[COMPLETED]** Write the user manual.

The system is now considered feature-complete and ready for beta testing and production deployment.
