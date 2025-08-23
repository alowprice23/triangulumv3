import time
import heapq
from dataclasses import dataclass, field
from typing import List, Any, Optional

from discovery.code_graph import CodeGraph

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
    """
    def __init__(self):
        self._queue: List[PrioritizedItem] = []

    def submit_ticket(self, ticket: BugTicket):
        """Adds a new bug ticket to the priority queue."""
        priority = calculate_priority(ticket)
        # We use negative priority because heapq is a min-heap.
        heapq.heappush(self._queue, PrioritizedItem(-priority, ticket))

    def get_next_ticket(self) -> BugTicket | None:
        """Retrieves the highest-priority bug ticket from the queue."""
        if not self._queue:
            return None
        return heapq.heappop(self._queue).item

    def is_empty(self) -> bool:
        """Checks if the scheduler queue is empty."""
        return not self._queue

    def __len__(self) -> int:
        return len(self._queue)
