import click
import requests
import time
import logging

# Configure logger for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"

def check_api_status():
    """Checks if the API is running."""
    try:
        response = requests.get(f"{API_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def submit_bug(description: str, severity: int) -> bool:
    """Submits a bug to the API."""
    logger.info(f"Submitting bug: '{description}'")
    try:
        response = requests.post(f"{API_URL}/bugs", json={"description": description, "severity": severity})
        if response.status_code == 202:
            logger.info("Bug submitted successfully. The supervisor is now processing it.")
            return True
        else:
            logger.error(f"Failed to submit bug. API returned status {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the API.")
        return False

def monitor_progress():
    """Polls the status endpoint and displays progress."""
    logger.info("Monitoring progress... (Press Ctrl+C to stop)")
    try:
        while True:
            response = requests.get(f"{API_URL}/status")
            if response.status_code == 200:
                status = response.json()
                queued = status['queued_tickets']
                active = status['active_sessions']
                logger.info(f"Status: {queued} ticket(s) queued, {active} session(s) active.")
                if queued == 0 and active == 0:
                    logger.info("Processing complete. The system is now idle.")
                    break
            else:
                logger.warning("Could not retrieve status from the API.")

            time.sleep(10) # Poll every 10 seconds
    except requests.exceptions.ConnectionError:
        logger.error("Connection to API lost.")
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user.")


@click.command(name="interactive")
def interactive_session():
    """
    Starts an interactive session to submit and monitor a bug fix.
    """
    logger.info("--- Triangulum Interactive Session ---")

    if not check_api_status():
        logger.error("The Triangulum API is not running. Please start it with 'docker-compose up --build'.")
        return

    description = click.prompt("Please describe the bug you want to fix", type=str)
    severity = click.prompt("Enter a severity for this bug (1-10)", type=int, default=5)

    if submit_bug(description, severity):
        monitor_progress()
