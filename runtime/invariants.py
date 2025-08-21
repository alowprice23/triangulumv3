from typing import List
from runtime.state import BugState, Phase

AGENT_POOL_SIZE = 9
AGENTS_PER_BUG = 3

class InvariantViolation(Exception):
    """Custom exception for invariant violations."""
    pass

def check_timer_non_negativity(bugs: List[BugState]):
    """Checks that all bug timers are non-negative."""
    for bug in bugs:
        if bug.timer < 0:
            raise InvariantViolation(f"Negative timer for bug: {bug.timer}")

def check_agent_capacity(bugs: List[BugState], free_agents: int):
    """Checks the agent capacity invariant."""
    active_bugs = sum(1 for bug in bugs if bug.phase in {Phase.REPRO, Phase.PATCH, Phase.VERIFY})
    if free_agents < 0:
        raise InvariantViolation(f"Negative free agents: {free_agents}")
    if free_agents + AGENTS_PER_BUG * active_bugs != AGENT_POOL_SIZE:
        raise InvariantViolation(
            f"Agent capacity invariant violated: "
            f"free_agents({free_agents}) + 3 * active_bugs({active_bugs}) != 9"
        )

def check_all_invariants(bugs: List[BugState], free_agents: int):
    """Checks all system invariants."""
    check_timer_non_negativity(bugs)
    check_agent_capacity(bugs, free_agents)
