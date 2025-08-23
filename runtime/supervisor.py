import time
from pathlib import Path

from runtime.scheduler import Scheduler, BugTicket
from runtime.pid import PIDController
from runtime.parallel_executor import ParallelExecutor
from runtime.allocator import Allocator

class Supervisor:
    """
    The Supervisor is the main control loop of the Triangulum runtime.
    It uses a Scheduler to prioritize work, a ParallelExecutor to run
    concurrent debugging sessions, and a PID controller to manage system load.
    """
    def __init__(self, max_concurrent_sessions: int = 3, repo_root: Path = None):
        self.scheduler = Scheduler()
        self.repo_root = repo_root
        self.is_running = False

        # Configure PID to maintain a backlog of around 5 tickets
        self.pid_controller = PIDController(Kp=0.1, Ki=0.01, Kd=0.05, setpoint=5)

        self.max_concurrent_sessions = max_concurrent_sessions

        # The Allocator manages the pool of agents available for assignment.
        self.allocator = Allocator()

        # The ParallelExecutor manages the thread pool for running Coordinators.
        self.executor = ParallelExecutor(max_workers=self.max_concurrent_sessions, allocator=self.allocator)

    def submit_bug(self, bug_description: str, severity: int):
        """Submits a new bug to the scheduler."""
        # Using timestamp for a simple unique ID. In a real system, use UUID.
        bug_id = str(time.time())
        ticket = BugTicket(bug_id=bug_id, severity=severity, description=bug_description)
        self.scheduler.submit_ticket(ticket)
        print(f"Supervisor: New bug ticket {ticket.bug_id} submitted with severity {severity}.")

    def tick(self):
        """
        Executes one cycle of the supervisor loop.
        """
        # 1. Check for and process any completed sessions
        completed_sessions = self.executor.check_completed_sessions()
        for bug_id, result in completed_sessions:
            status = result.get("status", "unknown")
            print(f"Supervisor: Session for bug {bug_id} finished with status: {status}.")
            # In a real system, we would log these results to a database.

        # 2. Update PID controller based on current backlog
        current_backlog = len(self.scheduler)
        pid_output = self.pid_controller.update(current_backlog)

        active_sessions = self.executor.get_active_session_count()
        print(f"Supervisor Tick: Backlog={current_backlog}, Active Sessions={active_sessions}, PID Output={pid_output:.2f}")

        # 3. Decide whether to spawn new sessions
        # Spawn if PID is positive, we have capacity, and there are tickets.
        should_spawn = pid_output > 0.2 and active_sessions < self.max_concurrent_sessions

        if not self.scheduler.is_empty() and should_spawn:
            next_ticket = self.scheduler.get_next_ticket()
            if next_ticket:
                print(f"Supervisor: Attempting to spawn new session for bug {next_ticket.bug_id}")
                launched = self.executor.launch_session(next_ticket, self.repo_root)
                if not launched:
                    # If launch fails (e.g., no agents), requeue ticket.
                    print(f"Supervisor: Failed to launch session for {next_ticket.bug_id}. Re-queuing.")
                    self.scheduler.submit_ticket(next_ticket)

    def run(self, duration_seconds: int):
        """
        Runs the supervisor loop for a given duration.
        """
        print(f"Supervisor: Starting main loop for {duration_seconds} seconds.")
        self.is_running = True
        end_time = time.time() + duration_seconds

        try:
            while self.is_running and time.time() < end_time:
                self.tick()
                time.sleep(5) # Tick every 5 seconds
        finally:
            self.stop()
            self.executor.shutdown()

        print("Supervisor: Main loop finished.")

    def stop(self):
        """Stops the supervisor loop."""
        self.is_running = False
