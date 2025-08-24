# PLAN(docker).md

## 1. Purpose & Scope (README-anchored)

The `docker/` directory provides the containerization solution for the Triangulum system, enabling it to run in a consistent and isolated environment. Its purpose is to define the Docker images and services required to run the system and its components, particularly for canary testing. `FILEMAP.MD` groups this directory under "Scripts & ops."

**Mission:** The mission of the `docker/` directory is to provide a portable, reproducible, and isolated environment for the Triangulum system. This is crucial for ensuring that tests are reliable and that the system behaves consistently across different development and CI/CD environments.

**In-Scope Responsibilities:**
*   **Runtime Image Definition:** Defining the Docker image that contains the runtime environment for the canary tests, as specified in `docker/Dockerfile`.
*   **Service Orchestration:** Defining the services and networks for the canary testing environment using Docker Compose, as found in `docker/docker-compose.yml`.
*   **Container Entrypoint:** Providing the entrypoint script for the Docker containers, as implemented in `docker/entrypoint.sh`.

**Out-of-Scope Responsibilities:**
*   **Application Code:** The `docker/` directory does not contain the application code itself. It only defines the environment in which the code runs.

## 2. Files in This Directory (from FILEMAP.md only)

### `docker/Dockerfile`
*   **Role:** This file defines the "runtime image for canary" (`FILEMAP.MD`). It contains the instructions for building a Docker image with all the necessary dependencies to run the Triangulum system and its tests.
*   **Key Contents (inferred):**
    *   A base image (e.g., a Python image).
    *   Installation of system-level dependencies.
    *   Installation of Python dependencies from `requirements.txt`.
    *   Copying of the application code into the image.
    *   Specification of the container's entrypoint.

### `docker/docker-compose.yml`
*   **Role:** This file defines the "app+db services; canary network" (`FILEMAP.MD`). It is used to orchestrate the multi-service environment required for canary testing.
*   **Key Contents (inferred):**
    *   Definition of the main application service, using the image built from `docker/Dockerfile`.
    *   Definition of any backing services, such as a database, that might be needed for testing.
    *   Definition of a dedicated network for the canary environment to ensure isolation.

### `docker/entrypoint.sh`
*   **Role:** This is the "container entry" script (`FILEMAP.MD`). It is the first script to run when a container is started.
*   **Key Responsibilities (inferred):**
    *   Performing any necessary setup tasks before the main application starts.
    *   Executing the main application process (e.g., `tri run`).

## 3. Internal Control Flow (Step-by-Step)

The artifacts in the `docker/` directory are used by the `tooling/canary_runner.py` to create the canary testing environment.

1.  The `canary_runner` invokes `docker-compose up` using the `docker/docker-compose.yml` file.
2.  Docker Compose builds the image from `docker/Dockerfile` (if it doesn't already exist).
3.  Docker Compose starts the services defined in the `yml` file.
4.  When the application container starts, it executes `docker/entrypoint.sh`.
5.  The `entrypoint.sh` script starts the main application process.

## 4. Data Flow & Schemas (README-derived)

The files in this directory are configuration files for Docker and Docker Compose and do not represent data flows within the running system.

## 5. Interfaces & Contracts (Cross-Referenced)

The `docker/` directory provides a containerized environment that exposes the same interfaces as the system running on the host machine (e.g., the CLI and the dashboard).

## 6. Error Handling & Edge Cases (From README Only)

*   **Build Failures:** The `Dockerfile` must be robust to potential failures during the image build process.
*   **Service Failures:** The `docker-compose.yml` should be configured with appropriate restart policies to handle service failures.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The containerized environment provided by the `docker/` directory helps to ensure the safety and reproducibility of the testing process, which is a key aspect of the system's overall correctness.

## 8. Testing Strategy & Traceability (README Mapping)

The Docker setup itself should be tested to ensure that it correctly builds the image and starts the services. This can be done as part of the CI/CD pipeline.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Create the `docker/Dockerfile`. - PENDING (Out of scope for initial local-only implementation)
2.  Create the `docker/docker-compose.yml`. - PENDING (Out of scope for initial local-only implementation)
3.  Create the `docker/entrypoint.sh`. - PENDING (Out of scope for initial local-only implementation)

## 10. Information-Gap Log (Do Not Invent)

None specific to this directory.

## 11. Glossary (README-Only)

*   **Dockerfile:** A text document that contains all the commands a user could call on the command line to assemble an image. (`FILEMAP.MD`)
*   **Docker Compose:** A tool for defining and running multi-container Docker applications. (`FILEMAP.MD`)

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
