from enum import Enum, auto
from dataclasses import dataclass

class Phase(Enum):
    """Represents the current phase of a bug in the debugging process."""
    WAIT = auto()
    REPRO = auto()
    PATCH = auto()
    VERIFY = auto()
    DONE = auto()
    ESCALATE = auto()

@dataclass(frozen=True, slots=True)
class BugState:
    """Represents the state of a single bug."""
    bug_id: str
    phase: Phase
    timer: int
    attempts: int
