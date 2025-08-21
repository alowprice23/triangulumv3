import subprocess
from pathlib import Path
import time
import requests
from typing import Tuple

def _check_docker_compose(repo_root: Path) -> bool:
    """Checks if docker-compose.yml exists."""
    return (repo_root / "docker-compose.yml").exists() or \
           (repo_root / "docker-compose.yaml").exists()

def start_canary(repo_root: Path, health_check_url: str = "http://localhost:8080") -> Tuple[bool, str]:
    """
    Starts a canary environment using docker-compose.

    Args:
        repo_root: The root directory of the repository.
        health_check_url: The URL to probe for a health check.

    Returns:
        A tuple of (success, message).
    """
    if not _check_docker_compose(repo_root):
        return False, "docker-compose.yml not found in repository root."

    try:
        # Start services in detached mode
        subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )

        # Health check
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(health_check_url, timeout=5)
                if response.status_code == 200:
                    return True, "Canary environment started successfully and is healthy."
            except requests.ConnectionError:
                time.sleep(5) # Wait for services to start up

        stop_canary(repo_root) # Clean up if health check fails
        return False, f"Health check failed after {max_retries} retries."

    except FileNotFoundError:
        return False, "The 'docker-compose' command is not installed or not in PATH."
    except subprocess.CalledProcessError as e:
        return False, f"docker-compose up failed: {e.stderr}"
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"


def stop_canary(repo_root: Path) -> Tuple[bool, str]:
    """
    Stops the canary environment.

    Args:
        repo_root: The root directory of the repository.

    Returns:
        A tuple of (success, message).
    """
    if not _check_docker_compose(repo_root):
        # Nothing to do if the file doesn't exist
        return True, "No docker-compose.yml found, assuming no canary environment to stop."

    try:
        subprocess.run(
            ["docker-compose", "down"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )
        return True, "Canary environment stopped successfully."
    except FileNotFoundError:
        return False, "The 'docker-compose' command is not installed or not in PATH."
    except subprocess.CalledProcessError as e:
        return False, f"docker-compose down failed: {e.stderr}"
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"
