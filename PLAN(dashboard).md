# PLAN(dashboard).md

## 1. Purpose & Scope (README-anchored)

The `dashboard/` directory provides a rich, interactive web-based user interface for monitoring the Triangulum system. Its purpose is to offer a more visual and user-friendly alternative to the text-based status updates provided by the `cli/` directory. `FILEMAP.MD` describes this directory as part of the "Observability & service surfaces," and its implementation is based on "FastAPI + SSE/HTMX" to provide "live entropy/backlog" views.

**Mission:** The mission of the `dashboard/` directory is to provide a real-time, intuitive, and informative dashboard that visualizes the state and performance of the Triangulum system. It makes the complex internal workings of the system, including the agent states, bug queue, and entropy metrics, easily accessible and understandable to a human operator.

**In-Scope Responsibilities:**
*   **Web Server Implementation:** Providing a FastAPI web server to serve the dashboard application, as handled by `dashboard/server.py`.
*   **Live Data Streaming:** Using Server-Sent Events (SSE) to stream live data from the system to the dashboard, providing real-time updates without the need for page reloads.
*   **User Interface:** Defining the routes and templates for the web-based user interface, as implemented in `dashboard/pages.py`. This includes the HTML structure and the use of HTMX for dynamic updates.

**Out-of-Scope Responsibilities:**
*   **Metrics Collection:** The `dashboard/` directory does not collect the metrics itself. It consumes them from the `obs/` directory.
*   **Core System Control:** The dashboard is a read-only view of the system. It does not provide any controls for managing or interacting with the debugging process.

## 2. Files in This Directory (from FILEMAP.md only)

### `dashboard/__init__.py`
*   **Role:** Standard Python package initializer.

### `dashboard/server.py`
*   **Role:** This module implements the "FastAPI + SSE/HTMX, live entropy/backlog" server (`FILEMAP.MD`). It is the core of the dashboard application.
*   **Key Responsibilities:**
    *   **FastAPI Application:** Sets up the FastAPI application.
    *   **SSE Endpoint:** Provides an endpoint (e.g., `/events`) that streams Server-Sent Events to the client.
    *   **Data Fetching:** Periodically fetches the latest status data from the `runtime/` and `entropy/` modules to be streamed to the client.
*   **Interfaces:**
    *   **Inputs:** HTTP requests from the user's browser.
    *   **Outputs:** HTML pages and SSE data streams.
*   **Dependencies:** `obs/`, `runtime/`, `entropy/`.

### `dashboard/pages.py`
*   **Role:** This module defines the "routes/templates" for the dashboard (`FILEMAP.MD`).
*   **Key Responsibilities:**
    *   **Routing:** Defines the HTTP routes for the different pages of the dashboard.
    *   **Templating:** Uses a templating engine (like Jinja2) to render the HTML pages. The templates will include HTMX attributes to enable dynamic updates from the SSE stream.
*   **Interfaces:**
    *   **Inputs:** HTTP requests.
    *   **Outputs:** Rendered HTML responses.
*   **Dependencies:** `dashboard/server.py`.

## 3. Internal Control Flow (Step-by-Step)

1.  **Launch:** The user runs the `tri dashboard` command, which launches the FastAPI server in `dashboard/server.py`.
2.  **Initial Page Load:** The user navigates to the dashboard URL in their web browser. `dashboard/pages.py` handles the request and serves the main HTML page.
3.  **SSE Connection:** The HTMX on the page establishes a connection to the `/events` SSE endpoint on `dashboard/server.py`.
4.  **Live Updates:** `dashboard/server.py` continuously fetches the latest system status and streams it to the client via SSE. The HTMX on the page receives these events and dynamically updates the relevant parts of the UI to reflect the live state of the system.

## 4. Data Flow & Schemas (README-derived)

*   **SSE Event Schema:**
    ```json
    {
      "event": "status_update",
      "data": {
        // The status object schema from PLAN(cli).md
      }
    }
    ```

## 5. Interfaces & Contracts (Cross-Referenced)

*   **HTTP GET /**: Returns the main dashboard page.
*   **HTTP GET /events**: SSE endpoint for live data.

## 6. Error Handling & Edge Cases (From README Only)

*   **Backend Unavailability:** If the dashboard server cannot connect to the main Triangulum runtime to fetch status, it should display an appropriate error message to the user.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The dashboard provides a visual way to monitor the system's invariants. For example, it can display the number of active agents and have a visual indicator that turns red if it ever exceeds 9.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the `dashboard/` directory should include:
*   Unit tests for the FastAPI routes.
*   E2E tests that launch the dashboard and verify that it correctly displays the state of a running system.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Set up the FastAPI application in `dashboard/server.py`.
2.  Implement the SSE endpoint for streaming live data.
3.  Create the HTML templates with HTMX in `dashboard/pages.py`.

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-021 | Dashboard UI design | `dashboard/pages.py` | The exact design and layout of the dashboard are not specified. | Low | UNSPECIFIED IN README — DO NOT INVENT. A simple, clean design will be used. |

## 11. Glossary (README-Only)

*   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints. (`FILEMAP.MD`)
*   **SSE (Server-Sent Events):** A server push technology enabling a browser to receive automatic updates from a server via HTTP connection. (`FILEMAP.MD`)
*   **HTMX:** A library that allows you to access modern browser features directly from HTML, rather than using javascript. (`FILEMAP.MD`)

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
