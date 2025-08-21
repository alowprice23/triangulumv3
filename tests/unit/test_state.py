import pytest
from runtime.state import Phase, BugState

def test_phase_enum():
    """Tests the members and length of the Phase enum."""
    assert Phase.WAIT.name == "WAIT"
    assert Phase.REPRO.name == "REPRO"
    assert Phase.PATCH.name == "PATCH"
    assert Phase.VERIFY.name == "VERIFY"
    assert Phase.DONE.name == "DONE"
    assert Phase.ESCALATE.name == "ESCALATE"
    assert len(Phase) == 6

def test_bug_state_dataclass():
    """Tests the instantiation and immutability of the BugState dataclass."""
    bug_state = BugState(bug_id="BUG-001", phase=Phase.WAIT, timer=0, attempts=0)
    assert bug_state.bug_id == "BUG-001"
    assert bug_state.phase == Phase.WAIT
    assert bug_state.timer == 0
    assert bug_state.attempts == 0

    # Check if the dataclass is frozen
    with pytest.raises(AttributeError):
        bug_state.phase = Phase.REPRO
