import json
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

class PerformanceRecord(BaseModel):
    """
    A structured record for the outcome of a single debugging session.
    """
    session_id: str
    timestamp: str
    final_status: str  # 'success' or 'failed'
    failure_reason: Optional[str] = None
    cycles_taken: int
    duration_seconds: float
    llm_provider: str
    llm_model: str
    initial_entropy: float
    information_gain: float
    human_suggestion_provided: bool
    successful_patch: Optional[str] = None

class PerformanceLogger:
    """
    Handles writing performance records to a persistent log file.
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Performance logger initialized for path: {self.log_path}")

    def log_session(self, record: PerformanceRecord):
        """
        Serializes a PerformanceRecord to JSON and appends it to the log file.
        """
        try:
            # Use `model_dump_json` which is the Pydantic v2 equivalent of `json()`
            record_json = record.model_dump_json()
            with self.log_path.open("a") as f:
                f.write(record_json + "\n")
        except Exception as e:
            logger.error(f"Failed to write performance record for session {record.session_id}: {e}", exc_info=True)
