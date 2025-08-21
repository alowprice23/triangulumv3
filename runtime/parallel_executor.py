import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List

from runtime.allocator import Allocator
from runtime.scheduler import BugTicket, Scheduler
from runtime.state import BugState, Phase

# Placeholder for the TriangulationEngine. In a complete implementation,
# this would be imported from its own module (e.g., runtime.engine).
class TriangulationEngine:
    def __init__(self, bugs: List[BugState]):
        self.bugs = bugs

    def execute_tick(self):
        # This would call the state transition logic.
        # For now, we'll simulate a bug's lifecycle.
        bug = self.bugs[0]
        if bug.phase == Phase.WAIT:
            bug.phase = Phase.REPRO
        elif bug.phase == Phase.REPRO:
            bug.phase = Phase.PATCH
        elif bug.phase == Phase.PATCH:
            bug.phase = Phase.VERIFY
        elif bug.phase == Phase.VERIFY:
            bug.phase = Phase.DONE

    def all_done(self) -> bool:
        return all(b.phase in {Phase.DONE, Phase.ESCALATE} for b in self.bugs)

# Placeholder for the AgentCoordinator.
class AgentCoordinator:
    async def coordinate_tick(self, engine: TriangulationEngine):
        # In a real implementation, this would orchestrate the O-A-V agents.
        await asyncio.sleep(0.01)


@dataclass
class BugContext:
    """Holds the context for a single, actively running bug."""
    engine: TriangulationEngine
    coordinator: AgentCoordinator

class ParallelExecutor:
    """
    Manages the concurrent execution of up to 3 bug-fixing processes.
    """
    MAX_CONCURRENT_BUGS = 3

    def __init__(self):
        self._scheduler = Scheduler()
        self._allocator = Allocator()
        self._active_bugs: Dict[str, BugContext] = {}
        self._backlog: Deque[BugTicket] = deque()

    def submit_ticket(self, ticket: BugTicket):
        """Adds a bug ticket to the backlog."""
        self._backlog.append(ticket)

    async def run(self, tick_interval: float = 0.1):
        """The main execution loop."""
        while True:
            self._schedule_backlog()
            self._launch_new_bugs()
            await self._run_active_bugs_tick()
            await asyncio.sleep(tick_interval)

    def _schedule_backlog(self):
        """Moves tickets from the backlog to the prioritized scheduler."""
        while self._backlog:
            self._scheduler.submit_ticket(self._backlog.popleft())

    def _launch_new_bugs(self):
        """Launches new bug-fixing processes if there is capacity."""
        while len(self._active_bugs) < self.MAX_CONCURRENT_BUGS:
            next_ticket = self._scheduler.get_next_ticket()
            if not next_ticket:
                break

            if self._allocator.allocate(next_ticket.bug_id):
                bug_state = BugState(
                    bug_id=next_ticket.bug_id,
                    phase=Phase.WAIT,
                    timer=0,
                    attempts=0,
                )
                engine = TriangulationEngine(bugs=[bug_state])
                coordinator = AgentCoordinator()
                self._active_bugs[next_ticket.bug_id] = BugContext(engine, coordinator)
            else:
                # If allocation fails, we should put the ticket back in the scheduler
                self._scheduler.submit_ticket(next_ticket)
                break

    async def _run_active_bugs_tick(self):
        """Runs one tick for each active bug-fixing process."""
        if not self._active_bugs:
            return

        completed_bug_ids = []
        for bug_id, context in self._active_bugs.items():
            context.engine.execute_tick()
            await context.coordinator.coordinate_tick(context.engine)

            if context.engine.all_done():
                completed_bug_ids.append(bug_id)

        for bug_id in completed_bug_ids:
            del self._active_bugs[bug_id]
            self._allocator.release(bug_id)
