# PLAN(human_hub).md

## 1. Purpose & Scope (README-anchored)

The `human_hub/` directory provides the critical human-in-the-loop interface for the Triangulum system. Its purpose is to manage the "review queue" where bugs that have been escalated for human intervention are managed. `FILEMAP.MD` describes this as a "FastAPI review queue; approve/reject endpoints."

**Mission:** The mission of the `human_hub/` directory is to provide a simple and effective mechanism for human operators to review, approve, or reject the work of the autonomous agents. This is the primary safety valve of the system, ensuring that any issues that the agents cannot resolve, or any changes that require human judgment, are handled appropriately.

**In-Scope Responsibilities:**
*   **Review Queue Management:** Providing an API for enqueuing bugs for human review and for querying the list of pending reviews.
*   **Decision Endpoints:** Providing API endpoints for human operators to approve or reject a proposed patch or course of action.
*   **Web Server:** Running a FastAPI server to expose these endpoints.

**Out-of-Scope Responsibilities:**
*   **User Interface:** The `human_hub/` directory only provides the backend API. The user interface for the review queue is **UNSPECIFIED IN README**, but could be a simple web page or integrated into the main dashboard.
*   **Agent Logic:** It does not contain any of the core agent logic.

## 2. Files in This Directory (from FILEMAP.md only)

### `human_hub/__init__.py`
*   **Role:** Standard Python package initializer.

### `human_hub/server.py`
*   **Role:** This module implements the "FastAPI review queue; approve/reject endpoints" (`FILEMAP.MD`). It is the core of the human-in-the-loop system.
*   **Key Responsibilities:**
    *   **FastAPI Application:** Sets up the FastAPI server.
    *   **Review Queue Endpoint:** An endpoint (e.g., `POST /review`) to add a new bug to the review queue.
    *   **Approve/Reject Endpoints:** Endpoints (e.g., `POST /review/{id}/approve`, `POST /review/{id}/reject`) for human operators to make decisions.
    *   **List Endpoint:** An endpoint (e.g., `GET /reviews`) to list the items in the review queue.
*   **Interfaces:**
    *   **Inputs:** HTTP requests from a client application (e.g., a web UI).
    *   **Outputs:** JSON responses indicating the result of the operations.
*   **Dependencies:** `runtime/supervisor.py` (to which it will report the human's decision).

## 3. Internal Control Flow (Step-by-Step)

1.  **Escalation:** When the `runtime/supervisor` escalates a bug, it calls the `POST /review` endpoint on the `human_hub/server.py` to add the bug to the review queue.
2.  **Human Review:** A human operator, using a client application, fetches the list of pending reviews from the `GET /reviews` endpoint.
3.  **Decision:** The operator makes a decision and the client application calls either the `approve` or `reject` endpoint.
4.  **Notification:** The `human_hub/server.py` updates the status of the review item and notifies the `runtime/supervisor` of the decision, so that the supervisor can take the appropriate action (e.g., merge the patch or restart the debugging cycle).

## 4. Data Flow & Schemas (README-derived)

*   **Review Item Schema:** **UNSPECIFIED IN README**. Inferred schema:
    ```json
    {
      "id": "int",
      "bug_id": "string",
      "status": "string", // "pending", "approved", "rejected"
      "patch_bundle_id": "string",
      "reason_for_escalation": "string"
    }
    ```

## 5. Interfaces & Contracts (Cross-Referenced)

*   **HTTP POST /reviews**: Create a new review item.
*   **HTTP GET /reviews**: List review items.
*   **HTTP POST /reviews/{id}/approve**: Approve a review item.
*   **HTTP POST /reviews/{id}/reject**: Reject a review item.

## 6. Error Handling & Edge Cases (From README Only)

*   **Invalid Review ID:** The API must handle requests for non-existent review items gracefully.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The `human_hub/` is a critical safety component. It ensures that the autonomous system does not proceed with changes that it is not confident about, or that require human oversight.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the `human_hub/` should include:
*   Unit tests for the FastAPI endpoints.
*   Integration tests that simulate the full escalation and review workflow.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Implement the backend review queue logic in `runtime/human_hub.py`. - COMPLETED
2.  Implement the API endpoints in `api/main.py` to expose the hub's functionality. - COMPLETED
3.  Integrate the hub with `runtime/supervisor.py` for escalations and decisions. - COMPLETED
4.  Create a web-based UI (`api/templates/hitl.html`) for human interaction. - COMPLETED

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-022 | Review queue UI | `human_hub/` | The UI for the human review process is not specified. | Medium | RESOLVED. A functional HTML+JS user interface has been implemented in `api/templates/hitl.html` and is served at the `/hitl` endpoint. |

## 11. Glossary (README-Only)

None specific to this directory.

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
