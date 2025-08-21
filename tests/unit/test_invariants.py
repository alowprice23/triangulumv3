import pytest
from runtime.state import BugState, Phase
from runtime.invariants import (
    check_timer_non_negativity,
    check_agent_capacity,
    InvariantViolation,
    AGENT_POOL_SIZE,
    AGENTS_PER_BUG,
)

def test_check_timer_non_negativity_valid():
    """Test that check_timer_non_negativity passes with valid timers."""
    bugs = [
        BugState(bug_id="BUG-001", phase=Phase.WAIT, timer=0, attempts=0),
        BugState(bug_id="BUG-002", phase=Phase.REPRO, timer=3, attempts=0),
    ]
    try:
        check_timer_non_negativity(bugs)
    except InvariantViolation:
        pytest.fail("check_timer_non_negativity raised InvariantViolation unexpectedly.")

def test_check_timer_non_negativity_invalid():
    """Test that check_timer_non_negativity raises an exception for negative timers."""
    bugs = [
        BugState(bug_id="BUG-001", phase=Phase.WAIT, timer=0, attempts=0),
        BugState(bug_id="BUG-002", phase=Phase.REPRO, timer=-1, attempts=0),
    ]
    with pytest.raises(InvariantViolation):
        check_timer_non_negativity(bugs)

def test_check_agent_capacity_valid():
    """Test that check_agent_capacity passes with a valid agent configuration."""
    bugs = [
        BugState(bug_id="BUG-001", phase=Phase.REPRO, timer=3, attempts=0),
        BugState(bug_id="BUG-002", phase=Phase.PATCH, timer=2, attempts=0),
    ]
    free_agents = AGENT_POOL_SIZE - (2 * AGENTS_PER_BUG)
    try:
        check_agent_capacity(bugs, free_agents)
    except InvariantViolation:
        pytest.fail("check_agent_capacity raised InvariantViolation unexpectedly.")

def test_check_agent_capacity_invalid_too_many_active():
    """Test that check_agent_capacity raises an exception for too many active bugs."""
    bugs = [
        BugState(bug_id="BUG-001", phase=Phase.REPRO, timer=3, attempts=0),
        BugState(bug_id="BUG-002", phase=Phase.PATCH, timer=2, attempts=0),
        BugState(bug_id="BUG-003", phase=Phase.VERIFY, timer=1, attempts=0),
    ]
    free_agents = 1  # Should be 0
    with pytest.raises(InvariantViolation):
        check_agent_capacity(bugs, free_agents)

def test_check_agent_capacity_invalid_negative_free_agents():
    """Test that check_agent_capacity raises an exception for negative free agents."""
    bugs = [BugState(bug_id="BUG-001", phase=Phase.REPRO, timer=3, attempts=0)]
    free_agents = -1
    with pytest.raises(InvariantViolation):
        check_agent_capacity(bugs, free_agents)

def test_check_agent_capacity_valid_no_active_bugs():
    """Test that check_agent_capacity passes when there are no active bugs."""
    bugs = [
        BugState(bug_id="BUG-001", phase=Phase.WAIT, timer=0, attempts=0),
        BugState(bug_id="BUG-002", phase=Phase.DONE, timer=0, attempts=0),
    ]
    free_agents = AGENT_POOL_SIZE
    try:
        check_agent_capacity(bugs, free_agents)
    except InvariantViolation:
        pytest.fail("check_agent_capacity raised InvariantViolation unexpectedly.")
