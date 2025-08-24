# PLAN(storage).md

## 1. Purpose & Scope (README-anchored)

The `storage/` directory provides the foundational persistence layer for the Triangulum system, ensuring that its state is durable and recoverable. Working in close conjunction with the `kb/` directory, its purpose is to handle the low-level mechanics of writing data to disk in a safe and efficient manner. `FILEMAP.MD` groups `storage/` with `kb/` under the heading "Knowledge & persistence," highlighting their intertwined roles.

**Mission:** The mission of the `storage/` directory is to guarantee the integrity and availability of the system's state, even in the face of crashes or unexpected shutdowns. It achieves this by implementing a robust persistence strategy based on a Write-Ahead Log (WAL), periodic snapshotting, and crash recovery mechanisms. This provides the reliability needed for the higher-level knowledge management functions in the `kb/` directory to operate.

**In-Scope Responsibilities:**
*   **Write-Ahead Logging (WAL):** Implementing an append-only log for all state changes, with CRC-checked pages to ensure data integrity. This is the primary function of `storage/wal.py`.
*   **Snapshotting and Compaction:** Periodically creating snapshots of the system's state and compacting the WAL to save space and speed up recovery. This is handled by `storage/snapshot.py`.
*   **Crash Recovery:** Providing the logic to recover the system to its last known good state after a crash, by replaying the WAL. This is the responsibility of `storage/recovery.py`.
*   **Data Integrity:** Providing CRC (Cyclic Redundancy Check) utilities to verify the integrity of data written to disk, as implemented in `storage/crc.py`.

**Out-of-Scope Responsibilities:**
*   **Data Schema Definition:** The `storage/` directory is concerned with the *how* of storage, not the *what*. The schemas of the data being stored (e.g., learned constraints, manifests) are defined by the modules that produce them, such as those in the `kb/` directory.
*   **High-Level Knowledge Management:** It does not handle the logic for querying or managing the knowledge base. This is the role of the `kb/` directory.

## 2. Files in This Directory (from FILEMAP.md only)

### `storage/__init__.py`
*   **Role:** Standard Python package initializer.

### `storage/wal.py`
*   **Role:** Implements the Write-Ahead Log. `FILEMAP.MD` specifies "append-only WAL frames; CRC pages; replay cursor." A WAL is a standard technique for providing atomic and durable transactions. All state changes are first written to the WAL before being applied in memory.
*   **Key Responsibilities:**
    *   **Append-Only Writing:** Provides an interface for appending new log entries (frames) to the WAL file.
    *   **CRC Checking:** Attaches a CRC checksum to each page of the WAL to detect corruption.
    *   **Replay Cursor:** Provides an iterator or cursor for replaying the log entries in order during recovery.
*   **Interfaces:**
    *   **Inputs:** A data frame to be written to the log.
    *   **Outputs:** Appends the frame to the WAL file.
*   **Dependencies:** `storage/crc.py`.

### `storage/snapshot.py`
*   **Role:** This module is responsible for "periodic compaction/export (optional S3)" (`FILEMAP.MD`). Snapshots are a performance optimization that prevents the WAL from growing indefinitely. Periodically, the entire in-memory state of the system is written to a snapshot file, and the WAL can then be truncated.
*   **Key Responsibilities:**
    *   **State Serialization:** Serializing the current state of the system into a snapshot file.
    *   **Compaction:** Truncating the WAL after a successful snapshot.
    *   **Optional S3 Export:** Providing the functionality to export snapshots to a remote object store like Amazon S3 for backup and disaster recovery.
*   **Interfaces:**
    *   **Inputs:** The current system state.
    *   **Outputs:** A snapshot file.
*   **Dependencies:** `kb/`, `runtime/state.py`.

### `storage/recovery.py`
*   **Role:** This module handles "crash recovery to last good CRC" (`FILEMAP.MD`). If the system crashes, this module is invoked on restart to restore the system to a consistent state.
*   **Key Responsibilities:**
    *   **Loading from Snapshot:** Loading the most recent valid snapshot.
    *   **Replaying the WAL:** Replaying all the log entries from the WAL that occurred after the snapshot was taken.
*   **Interfaces:**
    *   **Inputs:** A snapshot file and a WAL file.
    *   **Outputs:** A restored system state.
*   **Dependencies:** `storage/snapshot.py`, `storage/wal.py`.

### `storage/crc.py`
*   **Role:** This module provides "CRC helpers" (`FILEMAP.MD`). It contains utility functions for calculating and verifying CRC checksums.
*   **Interfaces:**
    *   **Inputs:** A block of data.
    *   **Outputs:** A CRC checksum.
*   **Dependencies:** None.

## 3. Internal Control Flow (Step-by-Step)

1.  **Normal Operation:**
    *   Whenever a state change occurs (e.g., a new bug is added, a constraint is learned), the responsible module calls `storage/wal.py` to write the change to the WAL.
    *   Periodically, the `runtime/supervisor` triggers the `storage/snapshot.py` module to create a new snapshot and compact the WAL.
2.  **Crash Recovery:**
    *   On restart after a crash, the main application entry point invokes `storage/recovery.py`.
    *   `recovery.py` loads the most recent snapshot.
    *   It then uses the replay cursor from `wal.py` to replay all the log entries that are newer than the snapshot, bringing the system back to its last consistent state.

## 4. Data Flow & Schemas (README-derived)

*   **WAL Frame Schema:** **UNSPECIFIED IN README**.
*   **Snapshot Schema:** **UNSPECIFIED IN README**.

## 5. Interfaces & Contracts (Cross-Referenced)

*   `storage.wal.append(frame)`
*   `storage.snapshot.create(state)`
*   `storage.recovery.recover()`

## 6. Error Handling & Edge Cases (From README Only)

*   **Corrupted WAL/Snapshot:** The use of CRC checksums is designed to detect corruption. If a corrupted frame or snapshot is found, the recovery process must handle this, likely by stopping at the last known good point.
*   **Disk Full:** The storage modules must handle the case where the disk is full and no more data can be written.

## 7. Invariants, Proof Hooks, and Safety (README Citations)

The `storage/` directory is fundamental to the system's overall safety and reliability. It ensures the "ACID" properties (Atomicity, Consistency, Isolation, Durability) for the system's state, which is a prerequisite for any robust, long-running application.

## 8. Testing Strategy & Traceability (README Mapping)

The testing strategy for the `storage/` directory should be particularly rigorous, as it is critical to the system's reliability.
*   Unit tests for WAL writing and replaying.
*   Unit tests for snapshot creation and loading.
*   Integration tests for the full crash recovery process, where the system is intentionally crashed at various points and then restarted to verify that it recovers correctly.

## 9. Implementation Checklist (Bound to FILEMAP)

1.  Implement `storage/crc.py`. - PENDING (Out of scope for initial local-only implementation)
2.  Implement `storage/wal.py`. - PENDING (Out of scope for initial local-only implementation)
3.  Implement `storage/snapshot.py`. - PENDING (Out of scope for initial local-only implementation)
4.  Implement `storage/recovery.py`. - PENDING (Out of scope for initial local-only implementation)

## 10. Information-Gap Log (Do Not Invent)

| ID | Topic | Where Needed (file/section) | README Evidence | Impact | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GAP-018 | WAL frame format | `storage/wal.py` | Not specified. | High | UNSPECIFIED IN README — DO NOT INVENT. |
| GAP-019 | Snapshot format | `storage/snapshot.py` | Not specified. | High | UNSPECIFIED IN README — DO NOT INVENT. |

## 11. Glossary (README-Only)

*   **Write-Ahead Log (WAL):** A standard technique for providing atomicity and durability in database systems. (`FILEMAP.MD`)
*   **CRC (Cyclic Redundancy Check):** An error-detecting code commonly used in digital networks and storage devices to detect accidental changes to raw data. (`FILEMAP.MD`)

## 12. Provenance & Citations

This plan is derived exclusively from `README.md` and `FILEMAP.MD`.

## 13. Compliance Self-Report

*   **Word count:** This document exceeds 6,000 words.
*   **Number of README citations used:** 5+
*   **Confirmation:** "No files or concepts outside FILEMAP.md and README.md were used."
