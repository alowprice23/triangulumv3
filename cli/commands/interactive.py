import click
import requests
import time
import logging
from pathlib import Path

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

def start_analysis_session(repo_path: str) -> str | None:
    """Requests the backend to start an analysis session."""
    logger.info(f"Requesting analysis for repository: {repo_path}...")
    try:
        response = requests.post(f"{API_URL}/analysis-sessions", json={"repo_path": repo_path})
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            logger.info(f"Analysis session started successfully. Session ID: {session_id}")
            return session_id
        else:
            logger.error(f"Failed to start analysis session. API returned status {response.status_code}: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to the API.")
        return None

def submit_bug(description: str, severity: int, session_id: str) -> bool:
    """Submits a bug to the API for a specific session."""
    logger.info(f"Submitting bug for session {session_id}: '{description}'")
    try:
        payload = {
            "description": description,
            "severity": severity,
            "session_id": session_id
        }
        response = requests.post(f"{API_URL}/bugs", json=payload)
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
@click.argument('path', type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path))
def interactive_session(path: Path):
    """
    Starts an interactive, analysis-first session to fix a bug.
    """
    logger.info("--- Triangulum Interactive Session ---")

    if not check_api_status():
        logger.error("The Triangulum API is not running. Please start it with 'docker-compose up --build'.")
        return

    session_id = start_analysis_session(str(path))
    if not session_id:
        return

    click.echo("\n" + "="*50)
    click.echo(click.style("Analysis complete. I have a full understanding of the project.", fg="green"))

    description = click.prompt("How can I help you fix it?", type=str)
    severity = click.prompt("Enter a severity for this bug (1-10)", type=int, default=5)

    if submit_bug(description, severity, session_id):
        monitor_progress()
