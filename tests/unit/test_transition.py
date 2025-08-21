import pytest
from runtime.state import BugState, Phase
from runtime.transition import transition_bug, TICKS_PER_PHASE

@pytest.fixture
def wait_bug():
    return BugState(bug_id="BUG-001", phase=Phase.WAIT, timer=0, attempts=0)

def test_wait_to_repro_with_agents(wait_bug):
    """Test transition from WAIT to REPRO when agents are available."""
    new_bug, agent_delta = transition_bug(wait_bug, 3)
    assert new_bug.phase == Phase.REPRO
    assert new_bug.timer == TICKS_PER_PHASE
    assert new_bug.attempts == 0
    assert agent_delta == -3

def test_wait_no_agents(wait_bug):
    """Test no transition from WAIT when no agents are available."""
    new_bug, agent_delta = transition_bug(wait_bug, 2)
    assert new_bug == wait_bug
    assert agent_delta == 0

def test_repro_to_patch():
    """Test transition from REPRO to PATCH when timer is 0."""
    bug = BugState(bug_id="BUG-001", phase=Phase.REPRO, timer=0, attempts=0)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == Phase.PATCH
    assert new_bug.timer == TICKS_PER_PHASE
    assert agent_delta == 0

def test_patch_to_verify():
    """Test transition from PATCH to VERIFY when timer is 0."""
    bug = BugState(bug_id="BUG-001", phase=Phase.PATCH, timer=0, attempts=0)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == Phase.VERIFY
    assert new_bug.timer == TICKS_PER_PHASE
    assert agent_delta == 0

def test_verify_first_attempt_fails():
    """Test that the first verification attempt fails and transitions to PATCH."""
    bug = BugState(bug_id="BUG-001", phase=Phase.VERIFY, timer=0, attempts=0)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == Phase.PATCH
    assert new_bug.timer == TICKS_PER_PHASE
    assert new_bug.attempts == 1
    assert agent_delta == 0

def test_verify_second_attempt_succeeds():
    """Test that the second verification attempt succeeds and transitions to DONE."""
    bug = BugState(bug_id="BUG-001", phase=Phase.VERIFY, timer=0, attempts=1)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == Phase.DONE
    assert new_bug.timer == 0
    assert new_bug.attempts == 0
    assert agent_delta == 3

def test_verify_third_attempt_escalates():
    """Test that a third verification attempt escalates."""
    bug = BugState(bug_id="BUG-001", phase=Phase.VERIFY, timer=0, attempts=2)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == Phase.ESCALATE
    assert new_bug.timer == 0
    assert new_bug.attempts == 0
    assert agent_delta == 3

@pytest.mark.parametrize("phase", [Phase.REPRO, Phase.PATCH, Phase.VERIFY])
def test_active_state_timer_decrement(phase):
    """Test that active states with timer > 0 just decrement the timer."""
    bug = BugState(bug_id="BUG-001", phase=phase, timer=2, attempts=0)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug.phase == phase
    assert new_bug.timer == 1
    assert agent_delta == 0

@pytest.mark.parametrize("phase", [Phase.DONE, Phase.ESCALATE])
def test_terminal_states_no_change(phase):
    """Test that terminal states do not change."""
    bug = BugState(bug_id="BUG-001", phase=phase, timer=0, attempts=0)
    new_bug, agent_delta = transition_bug(bug, 3)
    assert new_bug == bug
    assert agent_delta == 0
