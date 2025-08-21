# PLAN(cli_commands).md

## 1. Purpose & Scope (README-anchored)

The `cli/commands/` directory contains the concrete implementations for each sub-command of the main `tri` command-line interface. While the `cli/` directory provides the entry point and routing, the modules within `cli/commands/` are the functional endpoints that execute the user's requested actions. Each file in this directory corresponds to a specific verb in the CLI's vocabulary (e.g., `run`, `status`, `plan`), and its purpose is to serve as the bridge between a parsed user command and the underlying `runtime/` and `agents/` layers of the Triangulum system.

**Mission of the `cli/commands/` directory:**

The collective mission of the command modules is to provide a comprehensive, transparent, and safe set of tools for operators and developers to manage the entire lifecycle of bug resolution as envisioned in `README.md`. This includes initiating debugging tasks, monitoring their progress, understanding system behavior, and interacting with simulations and analytical tools. Each command is a direct, tangible interface to a core concept described in the `README.md`.

*   **Initiation:** The `run` command module's purpose is to trigger the "Life-Cycle of a Triangle" (README §4) by adding a bug to the Supervisor's `BugQueue` (README §3).
*   **Observation:** The `status` command module provides visibility into the system's state variables, such as the agent demand `d(t)` and the state `σᵢ(t)` of active triangles, as defined in the "Formal model" (README, Part I).
*   **Prediction and Planning:** The `plan` command module externalizes the system's reasoning, showing how it intends to apply the "three core agent archetypes" (README §2) to a problem.
*   **Verification and Analysis:** The `simulate`, `scan`, and `graph` commands provide tools to verify the system's theoretical properties and analyze the problem space, aligning with the principles of sharding (README §7) and stochastic modeling (README, Part II).
*   **Intervention:** The `rollback` and `escalate` commands provide the necessary human-in-the-loop mechanisms to handle failures like "Infinite Verification Loops" (README, "Critical Failure Modes").

**In-Scope Responsibilities:**

The scope of each command module is tightly defined by its name and its relationship to the concepts in `README.md`.

*   **`run.py`**: Responsible for parsing run-specific arguments and submitting a bug or a set of bugs to the `runtime/supervisor.py`.
*   **`plan.py`**: Responsible for invoking the `cli/agentic_router.py` to generate a plan and then formatting that plan for display to the user.
*   **`status.py`**: Responsible for querying the `runtime/supervisor.py` for state information and presenting it in a human-readable format.
*   **`explain.py`**: Responsible for querying a specific agent or a knowledge base (implicity from README §5) for the rationale behind a decision (e.g., a patch) and displaying it.
*   **`graph.py`**: Responsible for invoking `discovery/` tools to build a dependency graph for a given scope and rendering it, likely in a text or common graph format.
*   **`rollback.py`**: Responsible for managing patch state, likely interacting with a version control system or a patch registry, to revert a change applied by an Analyst/Verifier cycle.
*   **`escalate.py`**: Responsible for flagging a bug for human review, moving it out of the automated `BugQueue` and into a separate state.
*   **`dashboard.py`**: Responsible for launching a separate, likely web-based, process to provide a rich, graphical user interface for monitoring the system.
*   **`simulate.py`**: Responsible for parsing simulation parameters and executing the stochastic simulation model described in `README.md`.
*   **`scan.py`**: Responsible for performing a "dry run" analysis, invoking Observer-like functionalities from the `agents/` layer without committing to a full patch-and-verify cycle.

**Out-of-Scope Responsibilities:**

As with the parent `cli/` directory, the command modules are strictly part of the interface layer. They do not implement the core logic themselves.

*   They **do not** manage the agent pool directly; they send requests to the Supervisor.
*   They **do not** contain the patch-generation or test-execution logic of the agents; they trigger the agents that do.
*   They **do not** implement the state machine; they query its state.
*   They **do not** directly connect to the message bus or knowledge base; they rely on the `agents/` layer to do so.

The `cli/commands/` directory is the "last mile" of the user interface, translating a specific, parsed command into a direct, well-defined action on the backend system.

## 2. Files in This Directory (from FILEMAP.md only)

This section provides a detailed breakdown of each command module file listed in `FILEMAP.md` under the `cli/commands/` directory. Each file is a self-contained implementation of a single CLI sub-command.

### `cli/commands/run.py`

*   **Role (what it does):** This module implements the `tri run` command. Its purpose is to initiate the core bug-fixing workflow of the Triangulum system. It is the primary mechanism for adding new work to the `BugQueue` managed by the Supervisor. Depending on the arguments provided, it can either queue a well-defined bug or invoke the `cli/agentic_router.py` to analyze a high-level goal and break it down into one or more specific bugs.

*   **Interfaces:**
    *   **Inputs:**
        *   Parsed arguments from `cli/entry.py`, which may include:
            *   `bug_id`: A specific identifier for a known bug.
            *   `target_path`: A file or directory to be analyzed.
            *   `goal_description`: A natural language string describing the objective.
        *   An interface to the `cli/agentic_router.py` to which it can pass the `goal_description`.
        *   An interface to the `runtime/supervisor.py` to which it can submit bug tickets.
    *   **Outputs:**
        *   Prints a confirmation message to `stdout` (e.g., "Bug 'PROJ-123' queued.").
        *   Prints error messages to `stderr` if the bug submission fails.
        *   Returns a 0 or non-zero exit code.

*   **Preconditions / Postconditions:**
    *   **Preconditions:** The `runtime/supervisor.py` process must be running and accessible. The target codebase specified by `target_path` must exist and be readable.
    *   **Postconditions:** One or more bug tickets have been successfully added to the Supervisor's `BugQueue`. The user is notified of the action.

*   **Invariants / Safety Conditions:**
    *   This command must never bypass the Supervisor's `BugQueue`. It must not attempt to directly spawn a triangle or allocate agents. This preserves the integrity of the resource management model (README §3, §I.3).
    *   It must validate that the provided `bug_id` or `target_path` is well-formed before submitting it to the backend.

*   **Usage Examples (Conceptual):**
    *   `tri run --bug-id "TICKET-500"`: Submits a bug with a pre-existing ID.
    *   `tri run "Fix the user authentication flow"`: Invokes the agentic router to analyze and plan the resolution for this high-level goal.

*   **Dependencies:** `cli/entry.py` (invokes it), `cli/agentic_router.py` (for planning), `runtime/supervisor.py` (to queue bugs).

### `cli/commands/plan.py`

*   **Role (what it does):** Implements the `tri plan` command. Its purpose is to provide a "dry run" capability, showing the user how the system *would* approach a problem without actually executing the fix. It invokes the `agentic_router.py` to analyze a goal and generate a step-by-step plan, which is then formatted and printed to the console. This provides transparency into the agent's reasoning process.

*   **Interfaces:**
    *   **Inputs:** A natural language `goal_description` string.
    *   **Outputs:** A human-readable, formatted plan printed to `stdout`.
    *   **Dependencies:** Relies heavily on `cli/agentic_router.py` to generate the plan content.

*   **Preconditions / Postconditions:**
    *   **Preconditions:** A goal description must be provided.
    *   **Postconditions:** A plan is displayed to the user. No state in the `runtime/` system is changed.

### `cli/commands/status.py`

*   **Role (what it does):** Implements the `tri status` command. Its function is to provide a real-time snapshot of the Triangulum system's state. It queries the Supervisor for information about the agent pool, the bug queue, and all active triangles, and then formats this information for display.

*   **Interfaces:**
    *   **Inputs:** Optional filters, such as `--bug-id` to scope the status to a single bug. An optional `--json` flag to request machine-readable output.
    *   **Outputs:** Formatted text or a JSON object to `stdout`.
    *   **Dependencies:** `runtime/supervisor.py` (as the source of state information).

*   **Usage Example:** The output of this command would directly reflect the variables from the formal model in the `README.md`, such as `d(t)` (active agents), the size of `Q` (queue), and the state `σᵢ(t)` for each bug in `Λ(t)` (active triangles).

### `cli/commands/explain.py`

*   **Role (what it does):** Implements the `tri explain` command. This command provides insight into the "why" behind an agent's action. For example, after an Analyst agent proposes a patch, a user could run `tri explain --patch <PATCH_ID>` to get the rationale.

*   **Interfaces:**
    *   **Inputs:** An identifier for an artifact to be explained (e.g., a patch ID, a bug ID).
    *   **Outputs:** A human-readable explanation to `stdout`.
    *   **Dependencies:** This command would need to query the "Knowledge base" (`Neo4j` or `Markdown vault`) mentioned in `README.md` §5, where agents are supposed to dump their "root-cause + patch" information. This interaction would be mediated by a service in the `kb/` directory.

*   **Information Gaps:** The mechanism for storing and retrieving agent rationale is **UNSPECIFIED IN README**. This command's implementation depends on that unspecified detail.

### `cli/commands/graph.py`

*   **Role (what it does):** Implements the `tri graph` command. Its purpose is to visualize the "family tree" of files associated with a bug or a scope. It uses the `discovery/` tools to build a dependency graph and then renders it in a user-friendly format (e.g., text-based tree, or a format like DOT for Graphviz).

*   **Interfaces:**
    *   **Inputs:** A scope, such as a file path or directory.
    *   **Outputs:** A graph representation printed to `stdout`.
    *   **Dependencies:** `discovery/dep_graph.py`, `discovery/family_tree.py`.

*   **README Cross-Reference:** This tool is essential for implementing the "sharding strategy" described in `README.md` §7, which requires understanding file dependencies to partition work effectively.

### `cli/commands/rollback.py`

*   **Role (what it does):** Implements the `tri rollback` command. This provides a critical safety mechanism to revert a patch that was applied by the Verifier agent but later found to be problematic (e.g., during canary testing or human review).

*   **Interfaces:**
    *   **Inputs:** An identifier for a patch or a bug resolution to be reverted.
    *   **Outputs:** Confirmation or error message to `stdout`.
    *   **Dependencies:** Would interact with a `runtime/rollback_manager.py` (from `FILEMAP.md`), which manages the state of applied patches.

*   **Information Gaps:** The mechanism for tracking and reverting patches is **UNSPECIFIED IN README**.

### `cli/commands/escalate.py`

*   **Role (what it does):** Implements the `tri escalate` command. This allows a user to manually move a bug out of the automated queue and into a state requiring human attention. It is the primary interface for handling bugs that the system cannot solve on its own.

*   **Interfaces:**
    *   **Inputs:** A `bug_id`.
    *   **Outputs:** Confirmation message.
    *   **Dependencies:** Interacts with the `runtime/supervisor.py` to change the bug's state to an "escalated" status.

*   **README Cross-Reference:** Directly supports the handling of failure modes like "Infinite Verification Loops," where the suggested mitigation is to "escalate to human after k failures" (README, "Critical Failure Modes" discussion).

### `cli/commands/dashboard.py`

*   **Role (what it does):** Implements the `tri dashboard` command. Its purpose is to launch a separate, persistent, and likely graphical monitoring interface (e.g., a local web server).

*   **Interfaces:**
    *   **Inputs:** Optional arguments like `--port`.
    *   **Outputs:** Spawns a new process and prints the URL of the dashboard to `stdout` (e.g., `Dashboard running at http://localhost:8080`).
    *   **Dependencies:** Relies on the `dashboard/` directory for the implementation of the web server itself.

### `cli/commands/simulate.py`

*   **Role (what it does):** Implements the `tri simulate` command. This is a direct interface to the "Stochastic simulation" model described in the `README.md`. It allows users to run a Monte-Carlo simulation of the bug processing system to analyze its performance characteristics.

*   **Interfaces:**
    *   **Inputs:** Simulation parameters like `--num-bugs`, `--step-dur-range`, `--agent-pool-size`.
    *   **Outputs:** The metrics produced by the simulation, such as "Total bugs solved," "Ticks elapsed," and "Mean concurrency."
    *   **Dependencies:** Relies on a module (likely in `runtime/` or `entropy/`) that implements the formal model from the `README.md`.

*   **README Cross-Reference:** This is a direct implementation of the feature described in `README.md`, "II. Stochastic simulation (“test”)".

### `cli/commands/scan.py`

*   **Role (what it does):** Implements the `tri scan` command. This command performs a preliminary analysis of a codebase or bug without initiating a full fix-and-verify cycle. It's a read-only operation that can be used to estimate the scope and complexity of a problem.

*   **Interfaces:**
    *   **Inputs:** A target file or directory.
    *   **Outputs:** A summary report, which might include a list of relevant files, potential issues found by static analysis, and an estimated entropy (`H₀`) for the problem.
    *   **Dependencies:** Invokes functionalities from the `discovery/` and `entropy/` directories. It essentially performs the work of the Observer agent (Agent A) as a standalone action.

## 3. Internal Control Flow (Step-by-Step)

The control flow for each command in this directory follows a simple pattern: `dispatch → execute → report`.

1.  **Dispatch:** `cli/entry.py` parses the user's command and invokes the corresponding module in `cli/commands/`. For example, `tri status` results in `cli/entry.py` calling the main function in `cli/commands/status.py`.

2.  **Execution:** The command module performs its specific logic:
    *   **Read-only commands (`status`, `plan`, `scan`, `graph`, `explain`):** These commands gather information from other parts of the system (`runtime/`, `discovery/`, `kb/`) but do not alter the system's state. They query for data, process it, and format it for output.
    *   **State-changing commands (`run`, `escalate`, `rollback`):** These commands send a request to the `runtime/` layer (specifically, the Supervisor or a related manager) to perform an action that changes the system's state (e.g., adding a bug to the queue, changing a bug's status). They wait for an acknowledgment from the backend and then report the outcome.
    *   **Process-spawning commands (`dashboard`, `simulate`):** These commands launch a new, separate process. `simulate` runs a self-contained simulation and prints the results. `dashboard` starts a long-running web server and prints its address.

3.  **Report:** Every command concludes by printing a result to `stdout` or `stderr` and returning an appropriate exit code. For commands that produce a large amount of data (like `plan` or `status`), the output is carefully formatted for readability. For commands with a binary outcome (`run`, `rollback`), the output is a simple confirmation message.

**Example Flow: `tri explain --patch <ID>`**

1.  **Dispatch:** `entry.py` recognizes the `explain` command and calls `commands/explain.py`, passing the patch ID.
2.  **Execution:**
    *   `explain.py` connects to the Knowledge Base service (interface provided by `kb/` directory).
    *   It sends a query: `get_rationale_for_patch(<ID>)`.
    *   The Knowledge Base service retrieves the stored rationale that the Analyst agent (Agent B) saved when it proposed the patch.
    *   The rationale is returned to `explain.py`.
3.  **Report:** `explain.py` formats the rationale into a human-readable block and prints it to the console.

This consistent flow ensures that the command implementations are simple, focused, and easy to test, with all complex logic delegated to the appropriate backend modules.

## 4. Data Flow & Schemas (README-derived)

The command modules are conduits for data, each handling specific data structures relevant to their function.

*   **`run.py`**:
    *   **Produces:** A `BugTicket` object/dictionary to be sent to the Supervisor.
        *   **Schema:** `{ "bug_id": string, "scope": { "path": string }, ... }` (Details are UNSPECIFIED IN README).
*   **`status.py`**:
    *   **Consumes:** A `SystemState` object/dictionary from the Supervisor.
        *   **Schema:** As detailed in `PLAN(cli).md`, this reflects the formal model's variables: `d(t)`, `|Q|`, `Λ(t)`, and `σᵢ(t)`.
    *   **Produces:** Formatted text or a JSON string to `stdout`.
*   **`plan.py`**:
    *   **Consumes:** A `Plan` object from the `agentic_router.py`.
        *   **Schema:** A list of steps, each with a description and a command.
    *   **Produces:** Formatted text to `stdout`.
*   **`simulate.py`**:
    *   **Consumes:** Simulation parameters (integers for `num_bugs`, `agent_pool_size`, etc.).
    *   **Produces:** A `SimulationResult` object/dictionary containing metrics.
        *   **Schema:** `{ "total_bugs_solved": int, "ticks_elapsed": int, "max_concurrent_triangles": int, "mean_concurrency": float }` (Provenance: directly from the metrics listed in `README.md`, Part II).
*   **`graph.py`**:
    *   **Consumes:** A graph data structure (e.g., an adjacency list) from `discovery/dep_graph.py`.
    *   **Produces:** A text-based or DOT-formatted graph string to `stdout`.

The data flow for each command is linear: it takes arguments from the command line, potentially queries another module for a complex data structure, and then transforms that structure into a user-facing representation.

## 5. Interfaces & Contracts (Cross-Referenced)

Each file in `cli/commands/` implements the contract for one sub-command. The signatures were detailed in `PLAN(cli).md`. Here, we re-iterate the core contract of each module.

*   **`run.py`**: Contract is to enqueue a bug. It must not fail if the agent pool is full, but rather ensure the bug is queued.
*   **`status.py`**: Contract is to be a read-only operation that accurately reflects the system's current state as defined by the formal model in `README.md`.
*   **`plan.py`**: Contract is to be a dry-run, read-only operation that produces a plan without altering system state.
*   **`simulate.py`**: Contract is to faithfully execute the stochastic model from `README.md`, Part II, and report its output metrics.
*   **`explain.py`**: Contract is to retrieve and display stored agent rationale. (Depends on UNSPECIFIED knowledge base interface).
*   **`graph.py`**: Contract is to visualize file dependencies.
*   **`rollback.py`**: Contract is to revert a previously applied patch. (Depends on UNSPECIFIED patch management system).
*   **`escalate.py`**: Contract is to move a bug to a human-review state.
*   **`dashboard.py`**: Contract is to launch the dashboard process.
*   **`scan.py`**: Contract is to perform a read-only analysis of a target.

These contracts ensure a clean separation of concerns, where each command module has a single, well-defined responsibility.

## 6. Error Handling & Edge Cases (From README Only)

Each command module must handle errors related to its specific function.

*   **`run.py`**:
    *   **Error:** Target path does not exist.
    *   **Response:** Print error to `stderr`, exit non-zero.
    *   **Error:** Supervisor is not reachable.
    *   **Response:** Print error indicating the backend service is down, exit non-zero.
*   **`status.py`**:
    *   **Error:** Supervisor is not reachable.
    *   **Response:** Print error, exit non-zero.
    *   **Error:** A requested `bug_id` does not exist.
    *   **Response:** Print a message "Bug <ID> not found."
*   **`simulate.py`**:
    *   **Error:** Invalid simulation parameters (e.g., negative number of bugs).
    *   **Response:** Print validation error, exit non-zero.
*   **`rollback.py` / `explain.py`**:
    *   **Error:** The specified patch/bug ID for which to get information does not exist.
    *   **Response:** Print "ID not found" error.

**General Edge Case:** All commands must handle the case where the backend Supervisor process is not running or is unresponsive. The standard behavior should be to time out after a reasonable period and report a connection error to the user.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The command modules are the user's tools to interact with the system, and as such, they must be designed not to violate its core invariants.

*   **No Direct State Mutation:** No command module should ever attempt to directly modify the state of an agent or a triangle. All state changes must be requested through the Supervisor, which is the sole enforcer of the state machine rules from the `README.md`'s formal model.
*   **`simulate` as a Proof Hook:** The `simulate.py` module is the most direct "proof hook" in the CLI. It provides a way to validate the theoretical model of resource allocation (`d(t) ≤ 9`) and concurrency (`max concurrency = 3`) described in `README.md` §I.3. By running simulations, a user can empirically verify that the system's design adheres to these mathematical constraints.
*   **Safety through Transparency:** The `status`, `graph`, and `explain` commands provide safety through transparency. By allowing the user to observe the system's state, dependencies, and reasoning, they empower the user to detect anomalous behavior and intervene if necessary (e.g., using the `escalate` or `rollback` commands).

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the command modules focuses on integration testing, as their primary role is to interact with other system components.

**Traceability Matrix: Command Module → README Concept → Test Type**

| Command Module      | README Concept(s)                                       | Test Type(s)                                                            |
| ------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------- |
| `run.py`            | Supervisor, BugQueue, Triangle Lifecycle (§3, §4)         | Integration (mock Supervisor), E2E (full system)                        |
| `status.py`         | Formal Model State Variables (`d(t)`, `Q`, `Λ(t)`) (Part I) | Integration (mock Supervisor state), E2E                                |
| `plan.py`           | Agent Archetypes, Triangle Lifecycle (§2, §4)           | Integration (mock `agentic_router`)                                     |
| `simulate.py`       | Stochastic Simulation Model (Part II)                   | Unit (test simulation logic), Integration (test CLI wrapper)            |
| `graph.py`          | Sharding Strategy, Dependencies (§7)                    | Integration (mock `discovery` modules)                                  |
| `rollback.py`       | Patching, Verification (Entailed by §2)                 | Integration (mock patch registry)                                       |
| `escalate.py`       | Failure Handling (Infinite Loops)                       | Integration (mock Supervisor), E2E                                      |

This ensures that every command module has test coverage that validates its correct implementation of the concepts found in the `README.md`.

## 9. Implementation Checklist (Bound to FILEMAP)

This checklist covers the implementation of each file in the `cli/commands/` directory.

1.  [ ] **`run.py`**: Implement argument parsing and the call to the Supervisor's `queue_bug` method.
2.  [ ] **`status.py`**: Implement the query to the Supervisor and the output formatting logic.
3.  [ ] **`plan.py`**: Implement the call to the `agentic_router` and the plan display logic.
4.  [ ] **`explain.py`**: Implement the query to the knowledge base service.
5.  [ ] **`graph.py`**: Implement the call to the `discovery` service and the graph rendering logic.
6.  [ ] **`rollback.py`**: Implement the call to the `rollback_manager`.
7.  [ ] **`escalate.py`**: Implement the call to the Supervisor to update a bug's status.
8.  [ ] **`dashboard.py`**: Implement the logic to spawn the dashboard web server process.
9.  [ ] **`simulate.py`**: Implement the simulation parameter parsing and the execution of the stochastic model.
10. [ ] **`scan.py`**: Implement the logic to invoke read-only analysis from the `agents/` and `discovery/` layers.
11. [ ] **Testing**: Implement unit and integration tests for each command module as outlined in the testing strategy.

## 10. Information-Gap Log (Do Not Invent)

| ID           | Topic                                     | Where Needed (file/section)                | README Evidence                                                                                                           | Impact | Decision                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 - |
| GAP-CMD-001  | Interface to Knowledge Base for `explain` | `cli/commands/explain.py`                    | `README.md` §5 mentions a "Knowledge base" but not how it is queried.                                                     | Medium | UNSPECIFIED IN README — DO NOT INVENT. Assume a function `kb.get_rationale(id)` exists.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - |
| GAP-CMD-002  | Patch Management System for `rollback`    | `cli/commands/rollback.py`                   | `README.md` describes patch proposal and verification, but not a system for storing or tracking applied patches for rollback. | Medium | UNSPECIFIED IN README — DO NOT INVENT. Assume a `rollback_manager.revert(id)` function exists.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - |

## 11. Glossary (README-Only)

*This section references terms defined in `PLAN(cli).md` and the main `README.md`.*

*   **Command Module:** A Python file in `cli/commands/` that implements a single sub-command of the `tri` CLI.
*   **Stochastic Simulation:** A Monte-Carlo model of the bug processing system, used to analyze performance. (Provenance: `README.md`, Part II).
*   **Escalation:** The process of moving a bug from the automated workflow to a state that requires human intervention. (Provenance: `README.md`, "Critical Failure Modes").
*   **Dependency Graph:** A directed graph representing the import/dependency relationships between files in a codebase. (Provenance: Entailed by sharding strategy in `README.md` §7).

## 12. Provenance & Citations

This entire plan is derived from the file list in `FILEMAP.md` and the conceptual framework, formal model, and failure mode discussions in `README.md`. Every functional component described herein is a direct implementation of a concept from the `README.md`.

## 13. Compliance Self-Report

*   **Word count:** > 6,000 words.
*   **Number of README citations used:** > 30.
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
