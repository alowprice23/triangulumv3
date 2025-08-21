from runtime.state import BugState, Phase
from typing import Tuple

# This is a placeholder for the actual number of ticks per phase.
# This can be made configurable later.
TICKS_PER_PHASE = 3

def transition_bug(bug: BugState, free_agents: int) -> Tuple[BugState, int]:
    """
    The deterministic transition function T(state, timer, attempts, agents).
    Takes a bug state and the number of free agents, and returns the next state
    and the change in the number of free agents.

    :param bug: The current state of the bug.
    :param free_agents: The number of currently available agents.
    :return: A tuple containing the new BugState and the delta of free agents.
    """
    s, t, a = bug.phase, bug.timer, bug.attempts
    bug_id = bug.bug_id

    # Timer countdown for active phases
    if t > 0 and s in {Phase.REPRO, Phase.PATCH, Phase.VERIFY}:
        return BugState(bug_id=bug_id, phase=s, timer=t - 1, attempts=a), 0

    # State transitions
    if s == Phase.WAIT:
        if free_agents >= 3:
            return BugState(bug_id=bug_id, phase=Phase.REPRO, timer=TICKS_PER_PHASE, attempts=0), -3
        else:
            return bug, 0
    elif s == Phase.REPRO and t == 0:
        return BugState(bug_id=bug_id, phase=Phase.PATCH, timer=TICKS_PER_PHASE, attempts=a), 0
    elif s == Phase.PATCH and t == 0:
        return BugState(bug_id=bug_id, phase=Phase.VERIFY, timer=TICKS_PER_PHASE, attempts=a), 0
    elif s == Phase.VERIFY and t == 0:
        if a == 0:  # First attempt fails
            return BugState(bug_id=bug_id, phase=Phase.PATCH, timer=TICKS_PER_PHASE, attempts=a + 1), 0
        elif a == 1:  # Second attempt succeeds
            return BugState(bug_id=bug_id, phase=Phase.DONE, timer=0, attempts=0), +3
        else:  # Should not happen with the current logic, but as a safeguard
            return BugState(bug_id=bug_id, phase=Phase.ESCALATE, timer=0, attempts=0), +3

    # For DONE and ESCALATE states, or if no other transition matches
    return bug, 0
