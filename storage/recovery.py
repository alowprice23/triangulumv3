from typing import Dict, Any

from storage.wal import WriteAheadLog, LogEntryType
from storage.snapshot import SnapshotManager

class RecoveryManager:
    """
    Manages the recovery of the system's state from the WAL and snapshots.
    """
    def __init__(self, wal: WriteAheadLog, snapshot_manager: SnapshotManager):
        self._wal = wal
        self._snapshot_manager = snapshot_manager

    def recover_state(self) -> Dict[str, Any]:
        """
        Recovers the system's state by restoring the latest snapshot
        and replaying any subsequent WAL entries.

        Returns:
            The recovered state dictionary. If no snapshot or WAL is found,
            returns a default initial state.
        """
        print("RecoveryManager: Starting state recovery...")
        snapshot_id, state = self._snapshot_manager.restore_latest_snapshot()

        if state:
            print(f"RecoveryManager: Restored snapshot {snapshot_id}.")
            last_event_timestamp = int(snapshot_id)
        else:
            print("RecoveryManager: No valid snapshot found. Starting from empty state.")
            state = self._get_initial_state()
            last_event_timestamp = 0

        print("RecoveryManager: Replaying events from Write-Ahead Log...")
        events_replayed = 0
        for event in self._wal.read_events():
            # The bug_id is a timestamp we can use for ordering
            event_timestamp = self._get_event_timestamp(event)

            if event_timestamp > last_event_timestamp:
                self._apply_event(state, event)
                events_replayed += 1

        print(f"RecoveryManager: Replayed {events_replayed} events. Recovery complete.")
        return state

    def _get_event_timestamp(self, event: Dict[str, Any]) -> int:
        """
        Extracts a timestamp from a log event to ensure ordering.
        Returns 0 if the bug_id is not a valid timestamp.
        """
        try:
            # We'll use the bug_id, which is a timestamp, as the event's timestamp.
            return int(float(event["payload"]["bug_id"]))
        except (ValueError, KeyError):
            return 0

    def _apply_event(self, state: Dict[str, Any], event: Dict[str, Any]):
        """Applies a single log event to modify the current state."""
        entry_type = event.get("type")
        payload = event.get("payload", {})
        bug_id = payload.get("bug_id")

        if entry_type == LogEntryType.BUG_SUBMITTED:
            # Add the ticket to the scheduler's list
            # The list is a list of dicts, not BugTicket objects, for JSON serialization
            state["scheduler_tickets"].append(payload)
            print(f"  Replaying: BUG_SUBMITTED for {bug_id}")

        elif entry_type == LogEntryType.SESSION_LAUNCHED:
            # Move ticket from scheduler to active sessions
            state["scheduler_tickets"] = [
                t for t in state["scheduler_tickets"] if t["bug_id"] != bug_id
            ]
            state["active_sessions"][bug_id] = payload
            print(f"  Replaying: SESSION_LAUNCHED for {bug_id}")

        elif entry_type == LogEntryType.SESSION_COMPLETED:
            # Remove from active sessions OR scheduler queue
            if bug_id in state["active_sessions"]:
                del state["active_sessions"][bug_id]
            else:
                state["scheduler_tickets"] = [
                    t for t in state["scheduler_tickets"] if t["bug_id"] != bug_id
                ]
            print(f"  Replaying: SESSION_COMPLETED for {bug_id}")

    def _get_initial_state(self) -> Dict[str, Any]:
        """Returns the default initial state for the supervisor."""
        return {
            "scheduler_tickets": [],
            "active_sessions": {},
        }
