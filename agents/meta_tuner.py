import json
import time
import re
from pathlib import Path
from typing import Dict, Any

class MetaTuner:
    """
    The MetaTuner agent is responsible for learning from the outcomes of
    debugging cycles to improve the system's performance over time.
    """
    def __init__(self, log_file: str = "tuner_log.jsonl"):
        self.log_file = log_file

    def tune_from_outcome(
        self,
        final_result: Dict[str, Any],
        llm_config: Dict[str, Any]
    ) -> str | None:
        """
        Analyzes the outcome of a debugging session. If the cycle failed,
        it generates a "hint" to be used in the next attempt.
        """
        outcome = final_result.get("status")
        print(f"MetaTuner: Logging outcome: {outcome}")

        # Log the outcome as before
        log_entry = {
            "timestamp": time.time(),
            "outcome": outcome,
            "model_used": llm_config.get("model_name"),
            "rationale": final_result.get("rationale"),
            "final_reason": final_result.get("reason") or final_result.get("message")
        }
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError as e:
            print(f"MetaTuner: Error writing to log file: {e}")

        # If the cycle failed, generate a hint for the next attempt
        if outcome == "failed":
            reason = final_result.get("reason") or final_result.get("message", "unknown reason")
            print(f"MetaTuner: Generating hint from failed cycle. Reason: {reason}")

            # Construct the hint
            hint = f"Hint: A previous attempt to fix this bug failed. The reason was: '{reason}'. Do not repeat this mistake. Please analyze the problem carefully and suggest a different, more robust solution.\n\n"
            return hint

        return None
