from typing import Dict, Set

AGENT_POOL_SIZE = 9
AGENTS_PER_BUG = 3

class AllocationError(Exception):
    """Custom exception raised for allocation failures."""
    pass

class Allocator:
    """
    Manages the allocation of a finite pool of agents to bugs.

    This implementation is designed for a single-process, single-threaded or
    cooperative multitasking (asyncio) environment. For multi-threaded or
    multi-process scenarios, a lock or a more sophisticated distributed
    locking mechanism would be required to ensure atomicity.
    """
    def __init__(self):
        self._free_agents: int = AGENT_POOL_SIZE
        self._allocations: Dict[str, int] = {}

    def allocate(self, bug_id: str) -> bool:
        """
        Atomically allocates the required number of agents for a bug.
        Returns True if the allocation was successful, False otherwise.
        """
        if bug_id in self._allocations:
            raise AllocationError(f"Bug '{bug_id}' has already been allocated agents.")

        if self._free_agents >= AGENTS_PER_BUG:
            self._free_agents -= AGENTS_PER_BUG
            self._allocations[bug_id] = AGENTS_PER_BUG
            return True

        return False

    def release(self, bug_id: str):
        """
        Releases the agents held by a specific bug.
        If the bug holds no agents, this operation is a no-op.
        """
        if bug_id in self._allocations:
            self._free_agents += self._allocations.pop(bug_id)
            # Ensure we don't exceed the pool size due to logic errors
            if self._free_agents > AGENT_POOL_SIZE:
                self._free_agents = AGENT_POOL_SIZE


    @property
    def free_agents(self) -> int:
        """Returns the number of currently available agents."""
        return self._free_agents

    @property
    def allocated_bugs(self) -> Set[str]:
        """Returns the set of bug IDs that currently hold agents."""
        return set(self._allocations.keys())

    def __repr__(self) -> str:
        return (
            f"Allocator(free_agents={self.free_agents}, "
            f"allocated_to={len(self._allocations)} bugs)"
        )
