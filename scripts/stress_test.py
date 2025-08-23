import requests
import time
import threading
import logging

# Configure logger to print to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"
NUM_BUGS = 50
POLL_INTERVAL_SECONDS = 5

def submit_bug(bug_num: int):
    """Submits a single bug to the API."""
    payload = {
        "description": f"A new high-priority stress test bug #{bug_num}",
        "severity": 8
    }
    try:
        response = requests.post(f"{API_URL}/bugs", json=payload)
        if response.status_code == 202:
            logger.info(f"Successfully submitted bug #{bug_num}")
        else:
            logger.error(f"Failed to submit bug #{bug_num}: {response.status_code} {response.text}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to API at {API_URL}. Is the server running via docker-compose up?")
        return False
    return True

def monitor_status():
    """Polls the /status endpoint and prints the results."""
    while True:
        try:
            response = requests.get(f"{API_URL}/status")
            if response.status_code == 200:
                status = response.json()
                logger.info(f"[STATUS] Running: {status['is_running']}, Queued: {status['queued_tickets']}, Active: {status['active_sessions']}")
                if status['queued_tickets'] == 0 and status['active_sessions'] == 0:
                    logger.info("[STATUS] All bugs have been processed. Exiting monitor.")
                    break
            else:
                logger.error(f"[STATUS] Error fetching status: {response.status_code}")

            time.sleep(POLL_INTERVAL_SECONDS)
        except requests.exceptions.ConnectionError:
            logger.error(f"[STATUS] API is not responding. Exiting monitor.")
            break

def main():
    """Runs the stress test."""
    logger.info(f"--- Starting Stress Test: Submitting {NUM_BUGS} bugs ---")

    # Check if the API is running before we start
    try:
        requests.get(API_URL)
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to the API at {API_URL}.")
        logger.error("Please run 'docker-compose up --build' in another terminal before running this script.")
        return

    # Submit bugs
    for i in range(NUM_BUGS):
        if not submit_bug(i + 1):
            return # Stop if API is not available
        time.sleep(0.1) # Submit a bug every 100ms

    logger.info("\n--- All bugs submitted. Monitoring supervisor status... ---")
    monitor_status()

if __name__ == "__main__":
    main()
