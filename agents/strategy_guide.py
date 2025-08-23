import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from runtime.performance_logger import PerformanceRecord
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculates cosine similarity between two vectors."""
    if np.linalg.norm(vec_a) == 0 or np.linalg.norm(vec_b) == 0:
        return 0.0
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

class StrategyGuide:
    """
    Analyzes historical performance data to provide strategic advice to other agents.
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.performance_records: List[PerformanceRecord] = self._load_performance_log()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder="./embedding_cache")
        # Pre-compute embeddings for historical failure reasons for faster search
        self._compute_historical_embeddings()

    def _load_performance_log(self) -> List[PerformanceRecord]:
        """Loads all records from the performance log file."""
        if not self.log_path.is_file():
            logger.warning(f"Performance log file not found at {self.log_path}. Strategy guide will have no historical data.")
            return []

        records = []
        with self.log_path.open("r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    records.append(PerformanceRecord(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse performance log line: {line.strip()}. Error: {e}")

        logger.info(f"Loaded {len(records)} performance records for strategy analysis.")
        return records

    def _compute_historical_embeddings(self):
        """Generates and caches embeddings for the failure reasons in the historical data."""
        for record in self.performance_records:
            if record.failure_reason and not hasattr(record, '_failure_embedding'):
                # Attach the embedding to the record object for the lifetime of this instance.
                # This is a simple caching mechanism.
                record._failure_embedding = self.embedding_model.encode(record.failure_reason)

    def get_strategic_advice(self, current_error_log: str, top_k: int = 1) -> Optional[str]:
        """
        Provides strategic advice by finding the most similar successful past fix.

        Args:
            current_error_log: The error log of the current bug.
            top_k: The number of historical examples to provide.

        Returns:
            A formatted string containing the advice, or None if no relevant history is found.
        """
        if not self.performance_records or not current_error_log:
            return None

        current_error_embedding = self.embedding_model.encode(current_error_log)

        # Find successful records with similar failure reasons
        similarities = []
        for record in self.performance_records:
            # We are looking for successful fixes, so we compare the current error
            # to the 'failure_reason' of past *successful* runs. This seems counter-intuitive,
            # but the 'failure_reason' is what the bug *was*, so we want to find bugs
            # that looked like our current bug and were successfully fixed.
            # A better approach would be to log the initial error log.
            # For now, we will assume failure_reason of a successful task is the initial error.
            # Let's refine this: we should search through ALL records, and find the ones
            # that are most similar, and then check if they were successful.

            if hasattr(record, '_failure_embedding'):
                sim = _cosine_similarity(current_error_embedding, record._failure_embedding)
                similarities.append((record, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        # Filter for the top successful records
        top_successful_fixes = []
        for record, score in similarities:
            if record.final_status == 'success' and record.successful_patch:
                top_successful_fixes.append(record)
                if len(top_successful_fixes) >= top_k:
                    break

        if not top_successful_fixes:
            return None

        advice = "Based on historical data, a similar bug was fixed successfully. Consider this approach:\n"
        for fix in top_successful_fixes:
            advice += f"\n--- Example Fix for a similar error ---\n"
            advice += f"{fix.successful_patch}\n"
            advice += f"--- End of Example ---\n"

        return advice
