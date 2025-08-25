import time
import heapq
import json
from dataclasses import dataclass, field, asdict
from typing import List, Any, Optional
from pathlib import Path

from discovery.code_graph import CodeGraph
from storage.wal import WriteAheadLog, LogEntryType
from storage.snapshot import SnapshotManager
from storage.recovery import RecoveryManager

# Constants for the priority scoring function, as discussed in our chat history.
# These values are chosen to satisfy the starvation-freedom constraint.
ALPHA = 0.7  # Weight for severity
BETA = 0.3   # Weight for age
MAX_SEVERITY = 5
AGE_MAX_SECONDS = 3600 * 24  # 1 day for age to have maximum weight

@dataclass(order=True)
class PrioritizedItem:
    """Wrapper to store items in a priority queue."""
    priority: float
    item: Any = field(compare=False)

@dataclass
class BugTicket:
    """Represents a bug report before it enters the main engine."""
    bug_id: str
    severity: int
    description: str
    arrival_time: float = field(default_factory=time.time)
    code_graph: Optional[CodeGraph] = field(default=None, compare=False)

def calculate_priority(ticket: BugTicket) -> float:
    """
    Calculates a priority score for a bug ticket to prevent starvation.
    The formula is: priority = α * (severity/max_severity) + β * min(1, age/age_max)
    A higher score means higher priority.
    """
    # Normalized severity (0 to 1)
    normalized_severity = min(ticket.severity, MAX_SEVERITY) / MAX_SEVERITY

    # Normalized age (0 to 1)
    age_seconds = time.time() - ticket.arrival_time
    normalized_age = min(1.0, age_seconds / AGE_MAX_SECONDS)

    return (ALPHA * normalized_severity) + (BETA * normalized_age)

class Scheduler:
    """
    Manages the queue of incoming bugs, prioritizing them to prevent starvation.
    This version is integrated with the storage layer for persistence.
    """
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.wal = WriteAheadLog(storage_dir / "scheduler.wal")
        self.snapshot_manager = SnapshotManager(storage_dir / "scheduler_snapshots")
        self.recovery_manager = RecoveryManager(self.wal, self.snapshot_manager)
        self._queue: List[PrioritizedItem] = []
        self._recover_state()

    def _recover_state(self):
        """Recovers the scheduler's state from storage on initialization."""
        state = self.recovery_manager.recover_state()
        # The recovery manager returns a dict with 'scheduler_tickets'
        tickets_data = state.get("scheduler_tickets", [])
        for ticket_data in tickets_data:
            # Recreate BugTicket objects from dicts
            ticket = BugTicket(**ticket_data)
            priority = calculate_priority(ticket)
            heapq.heappush(self._queue, PrioritizedItem(-priority, ticket))

    def submit_ticket(self, ticket: BugTicket):
        """Adds a new bug ticket to the priority queue and logs it."""
        priority = calculate_priority(ticket)
        # We use negative priority because heapq is a min-heap.
        heapq.heappush(self._queue, PrioritizedItem(-priority, ticket))
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, asdict(ticket))

    def get_next_ticket(self) -> BugTicket | None:
        """Retrieves the highest-priority bug ticket and logs the session launch."""
        if not self._queue:
            return None
        ticket = heapq.heappop(self._queue).item
        self.wal.log_event(LogEntryType.SESSION_LAUNCHED, {"bug_id": ticket.bug_id})
        return ticket

    def complete_ticket(self, bug_id: str):
        """Logs the completion of a bug-fixing session."""
        self.wal.log_event(LogEntryType.SESSION_COMPLETED, {"bug_id": bug_id})

    def create_snapshot(self):
        """Creates a snapshot of the current scheduler queue."""
        # Convert BugTicket objects to dicts for JSON serialization
        tickets_data = [asdict(pi.item) for pi in self._queue]
        state = {"scheduler_tickets": tickets_data, "active_sessions": {}} # active_sessions handled by supervisor
        self.snapshot_manager.create_snapshot(state)
        # After snapshotting, we can potentially clear the WAL, but the WAL
        # implementation doesn't support that yet. This is a potential improvement.

    def is_empty(self) -> bool:
        """Checks if the scheduler queue is empty."""
        return not self._queue

    def __len__(self) -> int:
        return len(self._queue)
