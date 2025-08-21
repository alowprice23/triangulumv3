import pytest
from runtime.allocator import Allocator, AllocationError, AGENT_POOL_SIZE, AGENTS_PER_BUG

@pytest.fixture
def allocator():
    return Allocator()

def test_allocator_initial_state(allocator):
    """Test the initial state of the allocator."""
    assert allocator.free_agents == AGENT_POOL_SIZE
    assert not allocator.allocated_bugs

def test_allocator_allocate_success(allocator):
    """Test successful allocation of agents."""
    bug_id = "BUG-001"
    assert allocator.allocate(bug_id)
    assert allocator.free_agents == AGENT_POOL_SIZE - AGENTS_PER_BUG
    assert allocator.allocated_bugs == {bug_id}

def test_allocator_allocate_not_enough_agents(allocator):
    """Test that allocation fails when not enough agents are free."""
    # Allocate agents until none are left
    for i in range(AGENT_POOL_SIZE // AGENTS_PER_BUG):
        assert allocator.allocate(f"BUG-{i}")

    assert not allocator.allocate("BUG-LAST")
    assert allocator.free_agents == 0

def test_allocator_allocate_already_allocated(allocator):
    """Test that allocating agents for the same bug twice raises an exception."""
    bug_id = "BUG-001"
    allocator.allocate(bug_id)
    with pytest.raises(AllocationError):
        allocator.allocate(bug_id)

def test_allocator_release(allocator):
    """Test successful release of agents."""
    bug_id = "BUG-001"
    allocator.allocate(bug_id)
    allocator.release(bug_id)
    assert allocator.free_agents == AGENT_POOL_SIZE
    assert not allocator.allocated_bugs

def test_allocator_release_not_allocated(allocator):
    """Test that releasing agents for a bug that doesn't hold any is a no-op."""
    allocator.release("BUG-001")
    assert allocator.free_agents == AGENT_POOL_SIZE
    assert not allocator.allocated_bugs

def test_allocator_multiple_allocations_and_releases(allocator):
    """Test a sequence of allocations and releases."""
    bug1 = "BUG-001"
    bug2 = "BUG-002"

    assert allocator.allocate(bug1)
    assert allocator.free_agents == AGENT_POOL_SIZE - AGENTS_PER_BUG

    assert allocator.allocate(bug2)
    assert allocator.free_agents == AGENT_POOL_SIZE - 2 * AGENTS_PER_BUG

    allocator.release(bug1)
    assert allocator.free_agents == AGENT_POOL_SIZE - AGENTS_PER_BUG

    allocator.release(bug2)
    assert allocator.free_agents == AGENT_POOL_SIZE
