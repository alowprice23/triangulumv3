import json
import time
import re
from pathlib import Path
from typing import Dict, Any

class MetaTuner:
    """
    The MetaTuner agent is responsible for learning from the outcomes of
    debugging cycles to improve the system's performance over time by
    dynamically updating prompts.
    """
    def __init__(self, log_file: str = "tuner_log.jsonl"):
        self.log_file = log_file
        # Define the path to the prompts file relative to this file's location
        self.prompts_path = Path(__file__).parent / "prompts.py"

    def _read_analyst_prompt(self) -> str:
        """Reads the current ANALYST_PROMPT from the prompts.py file."""
        try:
            content = self.prompts_path.read_text(encoding="utf-8")
            # Use regex to find the multiline string assigned to ANALYST_PROMPT
            match = re.search(r"ANALYST_PROMPT\s*=\s*r?\"\"\"(.*?)\"\"\"", content, re.DOTALL)
            if match:
                return match.group(1)
        except (IOError, IndexError) as e:
            print(f"MetaTuner: Error reading prompts file: {e}")
        return ""

    def _write_analyst_prompt(self, new_prompt_content: str):
        """Writes the updated ANALYST_PROMPT back to the prompts.py file."""
        try:
            current_content = self.prompts_path.read_text(encoding="utf-8")
            # Use re.sub to replace the content of the multiline string
            new_file_content = re.sub(
                r"(ANALYST_PROMPT\s*=\s*r?\"\"\")(.*?)(\"\"\")",
                f"\\1{new_prompt_content}\\3",
                current_content,
                flags=re.DOTALL
            )
            self.prompts_path.write_text(new_file_content, encoding="utf-8")
            print("MetaTuner: Successfully updated ANALYST_PROMPT.")
        except IOError as e:
            print(f"MetaTuner: Error writing to prompts file: {e}")

    def tune_from_outcome(
        self,
        final_result: Dict[str, Any],
        llm_config: Dict[str, Any]
    ):
        """
        Analyzes the outcome of a debugging session and tunes the Analyst
        prompt if the cycle failed.
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

        # If the cycle failed, add a hint to the prompt for next time
        if outcome == "failed":
            reason = final_result.get("reason") or final_result.get("message", "unknown reason")
            print(f"MetaTuner: Debugging cycle failed. Tuning prompt with hint. Reason: {reason}")

            current_prompt = self._read_analyst_prompt()
            if not current_prompt:
                return

            # Construct the hint and prepend it to the prompt
            hint = f"Hint: The previous attempt to fix a similar bug failed. The reason was: '{reason}'. Please analyze the problem carefully and suggest a different, more robust solution.\n\n---\n\n"

            # Avoid adding duplicate hints
            if reason not in current_prompt:
                new_prompt = hint + current_prompt
                self._write_analyst_prompt(new_prompt)
