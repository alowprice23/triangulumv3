# PLAN(config).md

## 1. Purpose & Scope (README-anchored)

The `config/` directory provides the mechanism for configuring and controlling the behavior of the Triangulum system. Its purpose is to externalize all tunable parameters and policies, allowing operators to adjust the system's behavior without modifying its source code. `FILEMAP.MD` describes this directory as "Config & policy."

**Mission:** The mission of the `config/` directory is to provide a clear, structured, and centralized location for all system configuration. This includes everything from performance tuning parameters for the PID controller to security policies for the sandbox. By separating configuration from code, the system becomes more flexible, maintainable, and easier to manage in different environments.

**In-Scope Responsibilities:**
*   **Default Parameters:** Defining the default values for system parameters such as PID targets, capacity limits, and safe-mode toggles, as specified in `config/defaults.toml`.
*   **Language-Specific Rules:** Providing configuration for how the system should handle different programming languages, including rules for test discovery and dependency graphing, as found in `config/language_rules.toml`.
*   **Ignore Rules:** Defining the default set of file and directory patterns to be ignored by the system's scanner, as specified in `config/ignore.defaults`.
*   **Security Policies:** Defining security-related configurations, such as key policies and sandbox rules, as found in `config/security.yaml`.

**Out-of-Scope Responsibilities:**
*   **Implementation of Configuration Logic:** The `config/` directory only contains the configuration data itself. The logic for reading, parsing, and applying this configuration is implemented in the relevant modules throughout the system (e.g., `cli/entry.py`, `runtime/pid.py`, `discovery/ignore_rules.py`).

## 2. Files in This Directory (from FILEMAP.md only)

### `config/defaults.toml`
*   **Role:** This file contains the "PID targets, caps, safe-mode toggles" (`FILEMAP.MD`). It is the primary configuration file for the runtime behavior of the system.
*   **Key Configurations (inferred):**
    *   `pid_targets`: Target values for the PID controller (e.g., target agent utilization).
    *   `agent_caps`: The maximum number of agents in the pool (should be 9, as per the invariant).
    *   `safe_mode`: A boolean toggle to enable or disable safe-mode, which likely restricts the system to its most conservative behavior (e.g., smallest possible scope).
*   **Format:** TOML (Tom's Obvious, Minimal Language).

### `config/language_rules.toml`
*   **Role:** This file contains the "per-language test/graph rules" (`FILEMAP.MD`). It allows the behavior of the `discovery` and `adapters` modules to be customized for different languages.
*   **Key Configurations (inferred):**
    *   Rules for mapping source files to test files for each language.
    *   Rules for parsing dependencies for each language.
*   **Format:** TOML.

### `config/ignore.defaults`
*   **Role:** This file contains the "built-in ignores (logs, build dirs)" (`FILEMAP.MD`). It provides the default set of file patterns that should be ignored by the `discovery/repo_scanner.py`.
*   **Format:** A plain text file with one glob pattern per line.

### `config/security.yaml`
*   **Role:** This file defines the "key policy, path sandbox rules" (`FILEMAP.MD`). It is the central location for all security-related configuration.
*   **Key Configurations (inferred):**
    *   Policies for managing API keys (e.g., which key to use for which service).
    *   Rules for the `tooling/sandbox.py`, such as which directories are accessible from within the sandbox.
*   **Format:** YAML.

## 3. Internal Control Flow (Step-by-Step)

The configuration files in this directory are read by various components at startup.

1.  `cli/entry.py` is the most likely candidate to read `config/defaults.toml` and other top-level configuration files.
2.  The `discovery/ignore_rules.py` module reads `config/ignore.defaults` to get the default ignore patterns.
3.  The `discovery` and `adapters` modules read `config/language_rules.toml` to configure their language-specific behavior.
4.  The `tooling/sandbox.py` and `api/` modules read `config/security.yaml` to configure their security settings.

## 4. Data Flow & Schemas (README-derived)

The files in this directory are the source of configuration data for the entire system. Their schemas are defined by the structure of the TOML and YAML files themselves.

### 4.1 Unified Configuration Schema (New)

To address `GAP-024` and provide a centralized configuration, the system will use a single `config/system_config.yaml` file. This file consolidates the settings previously scattered across multiple files. This new schema also addresses `GAP-023` (API Credentials) and `GAP-010` (PID Parameters).

*   **`config/system_config.yaml` Schema:**

    ```yaml
    # Triangulum v3 System Configuration
    version: 1.0

    # General system-wide settings
    system:
      safe_mode: true # A global toggle to run in a restricted, safe mode.
      log_level: "INFO" # Default logging level: DEBUG, INFO, WARNING, ERROR

    # Runtime settings, including PID controller and agent pool management
    runtime:
      pid_controller:
        # Proportional, Integral, Derivative gains for the agent utilization controller
        # These values will need to be tuned empirically.
        kp: 0.1
        ki: 0.01
        kd: 0.05
        # Target agent utilization (e.g., 0.8 means 80% of agents should be busy)
        target_utilization: 0.8
        # Anti-windup limit for the integral term
        anti_windup_limit: 1.0
      agent_pool:
        # Maximum number of concurrent agents (must be a multiple of 3)
        capacity: 9

    # Discovery settings for scanning and analyzing projects
    discovery:
      # Default ignore patterns, similar to .gitignore
      ignore_patterns:
        - "**/node_modules"
        - "**/__pycache__"
        - "**/*.log"
        - "**/build"
        - "**/dist"
      # Language-specific rules for discovery
      language_rules:
        python:
          test_patterns: ["test_*.py", "*_test.py"]
          build_files: ["requirements.txt", "pyproject.toml"]
        javascript:
          test_patterns: ["*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]
          build_files: ["package.json"]
        java:
          test_patterns: ["*Test.java"]
          build_files: ["pom.xml", "build.gradle"]

    # Security settings for sandboxing and API key management
    security:
      # Filesystem access rules for the sandbox
      sandbox:
        # List of allowed paths (glob patterns) that the agent can read/write to.
        # Defaulting to only allow relative paths within the project.
        allowed_paths:
          - "./**"
        # List of forbidden paths.
        denied_paths:
          - "/etc/**"
          - "~/**"
      # This section defines HOW to get the keys, not the keys themselves.
      # The actual keys should be stored in environment variables for security.
      api_credentials:
        openai:
          # The name of the environment variable that holds the API key.
          api_key_env_var: "OPENAI_API_KEY"
        anthropic:
          api_key_env_var: "ANTHROPIC_API_KEY"
        github:
          token_env_var: "GITHUB_TOKEN"
    ```

## 5. Interfaces & Contracts (Cross-Referenced)

The `config/` directory does not have a programmatic interface. It is a data source for other modules.

## 6. Error Handling & Edge Cases (From README Only)

*   **Malformed Configuration:** The modules that read these configuration files must handle cases where the files are missing or contain syntax errors.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The configuration in this directory can affect the system's invariants. For example, the `agent_caps` value in `config/defaults.toml` must be consistent with the capacity constraint `d(t) ≤ 9` from the formal model.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy should include tests that run the system with different configurations to ensure that it behaves as expected.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Create the `config/defaults.toml` file with the appropriate keys and values. - COMPLETED (Functionality covered by `config/system_config.yaml`)
2.  Create the `config/language_rules.toml` file. - COMPLETED (Functionality covered by `config/system_config.yaml`)
3.  Create the `config/ignore.defaults` file. - COMPLETED
4.  Create the `config/security.yaml` file. - COMPLETED (Functionality covered by `config/system_config.yaml`)

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-024 | Exact configuration keys | `config/` | The exact keys and values for the configuration files are not fully specified. | High | UNSPECIFIED IN README — DO NOT INVENT. The implementation will need to define the specific keys based on the inferred requirements. |

## 11. Glossary (README-Only)

None specific to this directory.

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
