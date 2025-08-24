import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from agents.coordinator import Coordinator
from runtime.allocator import Allocator
from runtime.scheduler import BugTicket

logger = logging.getLogger(__name__)

@dataclass
class Session:
    """Holds the context for a single, actively running bug-fixing session."""
    ticket: BugTicket
    future: Future

class ParallelExecutor:
    """
    Manages the concurrent execution of multiple bug-fixing Coordinator sessions.
    """
    def __init__(self, max_workers: int, allocator: Allocator):
        self.max_workers = max_workers
        self._allocator = allocator
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._active_sessions: Dict[str, Session] = {}

    def launch_session(self, ticket: BugTicket, repo_root: Path) -> bool:
        """
        Launches a new coordinator session in a separate thread if resources are available.

        Returns:
            bool: True if the session was launched, False otherwise.
        """
        if len(self._active_sessions) >= self.max_workers:
            return False # Cannot launch, at capacity

        if not self._allocator.allocate(ticket.bug_id):
            return False # Cannot launch, no agents available

        logger.info(f"Executor: Launching session for bug {ticket.bug_id}")
        coordinator = Coordinator(repo_root=repo_root)

        # The coordinator's main loop is run in a separate thread
        future = self._executor.submit(
            coordinator.run_debugging_cycle,
            bug_description=ticket.description,
            code_graph=ticket.code_graph
        )

        session = Session(ticket=ticket, future=future)
        self._active_sessions[ticket.bug_id] = session
        return True

    def check_completed_sessions(self) -> List[Tuple[str, dict]]:
        """
        Checks for completed sessions, cleans them up, and returns their results.

        Returns:
            A list of tuples, where each tuple contains the bug_id and the
            result dictionary from a completed coordinator session.
        """
        completed = []
        finished_bug_ids = []

        for bug_id, session in self._active_sessions.items():
            if session.future.done():
                try:
                    result = session.future.result()
                    logger.info(f"Executor: Session for bug {bug_id} completed.")
                    completed.append((bug_id, result))
                except Exception as e:
                    logger.error(f"Executor: Session for bug {bug_id} failed with exception: {e}")
                    completed.append((bug_id, {"status": "failed", "reason": str(e)}))

                finished_bug_ids.append(bug_id)
                self._allocator.release(bug_id)

        # Remove finished sessions from the active dictionary
        for bug_id in finished_bug_ids:
            del self._active_sessions[bug_id]

        return completed

    def get_active_session_count(self) -> int:
        """Returns the number of currently active sessions."""
        return len(self._active_sessions)

    def shutdown(self):
        """Shuts down the thread pool executor."""
        logger.info("Executor: Shutting down...")
        self._executor.shutdown(wait=True)
