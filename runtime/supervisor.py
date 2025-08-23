import time
import logging
from pathlib import Path
from typing import Dict, Any

from runtime.scheduler import Scheduler, BugTicket
from runtime.pid import PIDController
from runtime.parallel_executor import ParallelExecutor
from runtime.allocator import Allocator
from storage.wal import WriteAheadLog, LogEntryType
from storage.snapshot import SnapshotManager
from storage.recovery import RecoveryManager
import runtime.metrics as metrics

logger = logging.getLogger(__name__)

class Supervisor:
    """
    The Supervisor is the main control loop of the Triangulum runtime.
    It uses a Scheduler, ParallelExecutor, and a persistence layer to provide
    a robust, stateful execution environment.
    """
    def __init__(self, max_concurrent_sessions: int = 3, repo_root: Path = None, state_dir: Path = Path("state")):
        self.repo_root = repo_root
        self.is_running = False
        self.ticks = 0
        self.snapshot_interval = 10 # Create a snapshot every 10 ticks

        # Setup persistence layer
        state_dir.mkdir(exist_ok=True)
        self.wal = WriteAheadLog(state_dir / "events.wal")
        self.snapshot_manager = SnapshotManager(state_dir / "snapshots")

        # Recover state before initializing other components
        recovery_manager = RecoveryManager(self.wal, self.snapshot_manager)
        initial_state = recovery_manager.recover_state()

        # Initialize components with recovered state
        self.scheduler = Scheduler()
        self.allocator = Allocator()
        self._initialize_from_state(initial_state)

        # Configure PID controller
        self.pid_controller = PIDController(Kp=0.1, Ki=0.01, Kd=0.05, setpoint=5)

        # Configure executor
        self.max_concurrent_sessions = max_concurrent_sessions
        self.executor = ParallelExecutor(max_workers=self.max_concurrent_sessions, allocator=self.allocator)

    def _initialize_from_state(self, state: Dict[str, Any]):
        """Populates the runtime components from a recovered state dict."""
        logger.info("Supervisor: Initializing from recovered state...")
        # Re-populate the scheduler's queue
        for ticket_data in state.get("scheduler_tickets", []):
            self.scheduler.submit_ticket(BugTicket(**ticket_data))

        # Sessions in 'active_sessions' from a snapshot were running before crash.
        # They did not complete, so we must re-queue them.
        for bug_id, session_data in state.get("active_sessions", {}).items():
            logger.info(f"Supervisor: Re-queuing incomplete session for bug {bug_id}")
            # We need the original ticket info to re-queue
            ticket_data = {
                "bug_id": bug_id,
                "severity": session_data.get("severity", 5), # Assume default if not present
                "description": session_data.get("description", "Recovered task"),
            }
            self.scheduler.submit_ticket(BugTicket(**ticket_data))

    def submit_bug(self, bug_description: str, severity: int) -> BugTicket:
        """
        Submits a new bug, ensuring it's logged before being scheduled.
        Returns the created ticket.
        """
        bug_id = str(time.time_ns()) # Use nanoseconds for higher precision
        ticket = BugTicket(bug_id=bug_id, severity=severity, description=bug_description)

        # Log the event first to ensure durability
        self.wal.log_event(
            LogEntryType.BUG_SUBMITTED,
            {"bug_id": ticket.bug_id, "severity": ticket.severity, "description": ticket.description}
        )

        self.scheduler.submit_ticket(ticket)
        metrics.BUGS_SUBMITTED.inc()
        logger.info(f"Supervisor: New bug ticket {ticket.bug_id} submitted.")
        return ticket

    def tick(self):
        """Executes one cycle of the supervisor loop."""
        self.ticks += 1

        # 1. Check for and process any completed sessions
        completed_sessions = self.executor.check_completed_sessions()
        for bug_id, result in completed_sessions:
            status = result.get("status", "unknown")
            logger.info(f"Supervisor: Session for bug {bug_id} finished with status: {status}.")
            self.wal.log_event(LogEntryType.SESSION_COMPLETED, {"bug_id": bug_id, "result": result})

            # Update metrics
            if status == "success":
                metrics.BUGS_FIXED_SUCCESS.inc()
            else:
                failure_reason = result.get("reason", "unknown")
                metrics.BUGS_FIXED_FAILURE.labels(reason=failure_reason).inc()

            # Record duration
            start_time_ns = int(float(bug_id))
            duration_s = (time.time_ns() - start_time_ns) / 1e9
            metrics.BUG_FIX_DURATION_SECONDS.observe(duration_s)

        # 2. Update gauges
        active_sessions_count = self.executor.get_active_session_count()
        current_backlog = len(self.scheduler)
        metrics.ACTIVE_SESSIONS.set(active_sessions_count)
        metrics.QUEUED_TICKETS.set(current_backlog)

        # 3. Update PID controller
        pid_output = self.pid_controller.update(current_backlog)

        # 4. Decide whether to spawn new sessions
        should_spawn = pid_output > 0.2 and active_sessions_count < self.max_concurrent_sessions

        if not self.scheduler.is_empty() and should_spawn:
            next_ticket = self.scheduler.get_next_ticket()
            if next_ticket:
                launched = self.executor.launch_session(next_ticket, self.repo_root)
                if launched:
                    logger.info(f"Supervisor: Launched session for bug {next_ticket.bug_id}")
                    self.wal.log_event(LogEntryType.SESSION_LAUNCHED, {"bug_id": next_ticket.bug_id, "description": next_ticket.description, "severity": next_ticket.severity})
                else:
                    self.scheduler.submit_ticket(next_ticket) # Re-queue if launch failed

        # 4. Periodic Snapshot
        if self.ticks % self.snapshot_interval == 0:
            logger.info("Supervisor: Creating periodic snapshot...")
            self.snapshot_manager.create_snapshot(self._get_current_state())

    def _get_current_state(self) -> Dict[str, Any]:
        """Gathers the current state of the system for snapshotting."""
        # Note: We don't snapshot the allocator state directly, as it's rebuilt
        # by the executor based on active sessions.
        return {
            "scheduler_tickets": [p_item.item.to_dict() for p_item in self.scheduler._queue],
            "active_sessions": {
                bug_id: {"description": session.future.arg_description} # A bit of a hack to get desc
                for bug_id, session in self.executor._active_sessions.items()
            }
        }

    def run(self, duration_seconds: int):
        """Runs the supervisor loop for a given duration."""
        logger.info(f"Supervisor: Starting main loop for {duration_seconds} seconds.")
        self.is_running = True
        end_time = time.time() + duration_seconds

        try:
            while self.is_running and time.time() < end_time:
                self.tick()
                time.sleep(5)
        finally:
            self.stop()

    def stop(self):
        """Stops the supervisor and performs a clean shutdown."""
        if self.is_running:
            logger.info("Supervisor: Shutting down...")
            self.is_running = False
            logger.info("Supervisor: Creating final snapshot.")
            self.snapshot_manager.create_snapshot(self._get_current_state())
            self.executor.shutdown()
            self.wal.close()
            logger.info("Supervisor: Shutdown complete.")

# Add to_dict to BugTicket for easier serialization
def ticket_to_dict(self):
    return {"bug_id": self.bug_id, "severity": self.severity, "description": self.description}
BugTicket.to_dict = ticket_to_dict

# A bit of a hack to get the description for snapshotting
def get_arg_description(self, *args, **kwargs):
    return args[0] if args else kwargs.get('description', 'N/A')

from concurrent.futures import Future
Future.arg_description = property(get_arg_description)
