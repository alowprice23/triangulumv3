import json
import logging
from collections import Counter
from pathlib import Path

# Configure logger to print to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

LOG_FILE = Path("tuner_log.jsonl")

def analyze_log():
    """
    Parses the tuner log file and prints a summary of performance metrics.
    """
    if not LOG_FILE.is_file():
        logger.error(f"Log file not found at: {LOG_FILE}")
        return

    total_cycles = 0
    success_count = 0
    failure_reasons = []

    with LOG_FILE.open("r") as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                total_cycles += 1
                if log_entry.get("outcome") == "success":
                    success_count += 1
                else:
                    reason = log_entry.get("final_reason")
                    if reason:
                        failure_reasons.append(reason)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode line: {line.strip()}")

    if total_cycles == 0:
        logger.info("Log file is empty. No data to analyze.")
        return

    success_rate = (success_count / total_cycles) * 100
    reason_counts = Counter(failure_reasons)

    logger.info("\n--- Tuning Log Analysis ---")
    logger.info(f"Total Cycles Run: {total_cycles}")
    logger.info(f"Success Rate: {success_rate:.2f}% ({success_count}/{total_cycles})")
    logger.info("\n--- Top 5 Failure Reasons ---")

    if not reason_counts:
        logger.info("No failures recorded.")
    else:
        for i, (reason, count) in enumerate(reason_counts.most_common(5)):
            logger.info(f"{i+1}. (x{count}) {reason}")
    logger.info("-" * 27)

if __name__ == "__main__":
    analyze_log()
