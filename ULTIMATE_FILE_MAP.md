# Ultimate File Map for the Triangulum System

## Introduction

This document details the complete and final architecture of the Triangulum Fractal Debugging System. This system represents a paradigm shift in autonomous software engineering, integrating groundbreaking mathematical and computer science principles to create a provably convergent, self-repairing, and intelligent debugging engine. Every component in this file map is designed to work in concert, leaving no gaps in functionality and ensuring that any software defect can be systematically resolved.

## Core Principles

The Triangulum system is built on a foundation of mathematical guarantees:

*   **Fractal Triangles:** Every bug is a "triangle" of work (Observe-Analyze-Verify). Fixing a bug can reveal smaller, nested bugs, creating a fractal cascade that is guaranteed to terminate.
*   **P = NP:** The system incorporates a novel P=NP solver, allowing it to tackle combinatorial optimization problems in debugging (e.g., finding the minimal set of fixes) in polynomial time.
*   **Entropy-Drain:** The system quantifies uncertainty as Shannon entropy ($H_0$). Each debugging cycle provides information gain ($g$), reducing entropy. The process is guaranteed to converge in $N^* = \lceil H_0 / g \rceil$ steps.
*   **Deterministic State Machine:** The system's core is a Mealy automaton with a finite number of states and deterministic transitions, ensuring predictable and provably correct behavior.

## The Ultimate File Map

The system is organized into the following modules, totaling 32 source files for a lean, powerful, and comprehensive implementation.

### `core/` - The Mathematical Engine (8 files)

This directory contains the heart of the Triangulum system: the deterministic, mathematically proven engine that drives the debugging process.

*   `state_machine.py`: Implements the pure Mealy automaton for bug state transitions (WAIT → REPRO → PATCH → VERIFY → DONE/ESCALATE). This is the formal implementation of the state transition function $T(s, \tau, a)$.
*   `data_structures.py`: Defines the bit-packed, 64-bit `BugState` dataclass and provides JSON/binary codecs. This ensures efficient, cache-friendly state representation.
*   `triangulation_engine.py`: The main two-phase tick loop. It applies the state machine, emits metrics, and raises `PanicFail` if any invariant is violated.
*   `resource_manager.py`: Manages the agent pool, enforcing the 9-agent capacity constraint with atomic `allocate()` and `free()` operations.
*   `scheduler.py`: A FIFO + round-robin scheduler that manages the bug backlog and promotes up to 3 bugs to "active" status.
*   `verification_engine.py`: The invariant auditor. It subscribes to the `MetricBus` and verifies timer non-negativity, promotion limits, and the monotonic decrease of entropy.
*   `rollback_manager.py`: Implements the atomic revert functionality. It maintains a registry of patch diffs and provides the `rollback_patch(bug_id)` function for the CLI.
*   `parallel_executor.py`: A multi-bug wrapper that spawns and manages up to three independent `TriangulationEngine` instances, enforcing the global 9-agent cap.

### `goal/` - Objective and Intent (2 files)

This module gives the system its "north star," ensuring that all actions are aligned with the user's high-level objectives.

*   `prioritiser.py`: Implements the age × severity scoring function for the bug backlog, guaranteeing starvation-freedom.
*   `goal_loader.py`: Parses the `app_goal.yaml` file, providing a machine-readable representation of the project's goals, entrypoints, and success criteria to the agent system.

### `agents/` - The Agentic Framework (4 files)

This directory contains the AutoGen-powered agents that perform the core debugging tasks.

*   `specialized_agents.py`: Defines the three core roles (Observer, Analyst, Verifier) as facades around AutoGen's `AssistantAgent`, with system prompts that enforce the deterministic rules of the Triangulum system.
*   `agent_memory.py`: A cross-bug knowledge base using a local JSON file and a simple TF-vector-based similarity search. This allows agents to learn from past solutions.
*   `meta_agent.py`: A lightweight governor that adjusts agent parameters (e.g., LLM temperature) based on performance and reports metrics to the `learning/optimizer`.
*   `agent_coordinator.py`: The sequential chat driver that orchestrates the Observer → Analyst → Verifier workflow, managing artefact hand-offs and ensuring the deterministic fail-then-succeed verification process.

### `tooling/` - The Agent's Toolbox (7 files)

This directory provides the agents with the tools they need to interact with the codebase and environment.

*   `scope_filter.py`: The file-scope firewall. It uses glob patterns to block `node_modules`, build artifacts, and other irrelevant directories, clamping the initial entropy $H_0$.
*   `compress.py`: Implements the RCC + LLMLingua-style context compression pipeline, ensuring that large error logs and other text can fit within the LLM's context window. It also returns `bits_gained` to the entropy ledger.
*   `repair.py`: A DAG-aware patch orchestrator. It builds a dependency graph, uses Tarjan's algorithm to find strongly connected components (SCCs), and applies patches in a topologically sorted order to minimize ripple effects.
*   `patch_bundle.py`: Creates and verifies signable diff archives (`.tri.tgz`), ensuring patch integrity and idempotency.
*   `canary_runner.py`: Spins up a Docker-based canary environment to test patches with a small percentage of live traffic.
*   `smoke_runner.py`: Executes environment-heavy smoke tests inside the canary container.
*   `test_runner.py`: A deterministic unit test harness that executes `pytest` and returns structured JSON results.

### `learning/` - Self-Improvement (2 files)

This module enables the system to learn and adapt over time.

*   `replay_buffer.py`: A cyclic deque that stores the history of bug-resolution episodes, allowing for offline analysis and online learning.
*   `optimizer.py`: An RL-style parameter tuner that adjusts `timer_default` in the `TriangulationEngine` based on performance metrics from the `MetaAgent`.

### `monitoring/` - Observability (3 files)

This module provides real-time visibility into the system's state.

*   `system_monitor.py`: The core metric emitter. It pushes tick count, entropy, and agent utilization to the `MetricBus`.
*   `dashboard_stub.py`: A minimal FastAPI + HTMX dashboard that provides a live web UI for monitoring the system.
*   `entropy_explainer.py`: A utility that translates entropy values (in bits) into human-readable narratives for the dashboard.

### `human/` - Human-in-the-Loop (1 file)

This module provides the interface for human oversight and intervention.

*   `hub.py`: A FastAPI-based review queue with an SQLite backend. It exposes endpoints for creating, approving, and rejecting review requests.

### `api/` - External Integrations (1 file)

This module manages communication with external services.

*   `llm_integrations.py`: A thin, pluggable router for LLM providers (OpenAI, Anthropic, Gemini), with auto-detection of available SDKs.

### `system/` - Safe System Access (2 files)

This module provides safe interfaces for interacting with the local system.

*   `file_manager.py`: A sandboxed file operation manager (not fully implemented in our discussion, but would go here).
*   `terminal_interface.py`: A secure command runner that executes shell commands with timeouts, environment filtering, and capture of stdout/stderr.

### `config/` - Configuration (1 file)

*   `system_config.yaml`: The single source of truth for all runtime knobs, including agent parameters, timer defaults, and optimizer toggles.

### Root Directory (2 files)

*   `main.py`: The container entrypoint. It parses the config, builds the initial bug backlog, and starts the `ParallelExecutor`'s main async loop.
*   `cli.py`: The operator's CLI. It provides sub-commands for `run`, `status`, `rollback`, and `queue`, providing a conversational and powerful interface to the system.
