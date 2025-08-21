import time
from typing import List

from runtime.scheduler import Scheduler, BugTicket
from runtime.pid import PIDController
# In a real system, the coordinator would likely be a separate process.
# Here we import it directly for simplicity.
from agents.coordinator import Coordinator
from pathlib import Path

class Supervisor:
    """
    The Supervisor is the main control loop of the Triangulum runtime.
    It uses a Scheduler to prioritize work and a PID controller to manage
    system load and agent allocation.
    """
    def __init__(self, max_concurrent_sessions: int = 3, repo_root: Path = None):
        self.scheduler = Scheduler()

        # Configure PID to maintain a backlog of around 5 tickets
        # Kp, Ki, Kd values would need to be tuned for a real system.
        self.pid_controller = PIDController(Kp=0.1, Ki=0.01, Kd=0.05, setpoint=5)

        self.max_concurrent_sessions = max_concurrent_sessions
        self.active_sessions: List[Coordinator] = []
        self.repo_root = repo_root # Assuming a single repo for now
        self.is_running = False

    def submit_bug(self, bug_description: str, severity: int):
        """Submits a new bug to the scheduler."""
        bug_id = str(time.time()) # Simple unique ID
        ticket = BugTicket(bug_id=bug_id, severity=severity, description=bug_description)
        self.scheduler.submit_ticket(ticket)
        print(f"Supervisor: New bug submitted with severity {severity}.")

    def tick(self):
        """
        Executes one cycle of the supervisor loop.
        """
        current_backlog = len(self.scheduler)
        pid_output = self.pid_controller.update(current_backlog)

        print(f"Supervisor Tick: Backlog={current_backlog}, PID Output={pid_output:.2f}")

        # Basic spawn policy:
        # If PID output is positive, we have capacity to do more work.
        # If negative, we should scale down or wait.
        should_spawn = pid_output > 0.2 and len(self.active_sessions) < self.max_concurrent_sessions

        if not self.scheduler.is_empty() and should_spawn:
            next_ticket = self.scheduler.get_next_ticket()
            if next_ticket:
                print(f"Supervisor: Spawning new session for bug {next_ticket.bug_id}")
                # In a real system, this would be a thread or process.
                # Here, we just create the object. We won't run the cycle here
                # as it would block the supervisor loop. This simulation assumes
                # the coordinator runs asynchronously.
                coordinator = Coordinator(repo_root=self.repo_root)
                self.active_sessions.append(coordinator)
                # coordinator.run_debugging_cycle(next_ticket.description)

        # In a real system, we would also check for completed sessions
        # and remove them from the active list.

    def run(self, duration_seconds: int):
        """
        Runs the supervisor loop for a given duration.
        """
        print("Supervisor: Starting main loop.")
        self.is_running = True
        end_time = time.time() + duration_seconds

        while self.is_running and time.time() < end_time:
            self.tick()
            time.sleep(5) # Tick every 5 seconds

        print("Supervisor: Main loop finished.")

    def stop(self):
        """Stops the supervisor loop."""
        self.is_running = False
