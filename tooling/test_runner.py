import json
from pathlib import Path
import tempfile
from typing import Dict, Any
import docker
import logging

logger = logging.getLogger(__name__)
TEST_RUNNER_IMAGE = "triangulum-test-runner"

def run_test_command(
    repo_root: Path,
    command: str
) -> Dict[str, Any]:
    """
    Runs a test command inside a secure, isolated Docker container and returns
    a structured JSON report.

    Args:
        repo_root: The root directory of the repository where the command will be run.
        command: The full test command string to execute.

    Returns:
        A dictionary containing the parsed JSON report from the test runner.
        Returns an error dictionary if the test execution fails.
    """
    try:
        client = docker.from_env()
        # Verify the test runner image exists
        client.images.get(TEST_RUNNER_IMAGE)
    except docker.errors.ImageNotFound:
        logger.error(f"Test runner Docker image not found: {TEST_RUNNER_IMAGE}")
        logger.error("Please build it first by running: docker build -t triangulum-test-runner -f test-runner.Dockerfile .")
        return {"error": f"Docker image {TEST_RUNNER_IMAGE} not found."}
    except docker.errors.DockerException as e:
        logger.error(f"Docker is not running or accessible: {e}")
        return {"error": "Docker daemon is not running or accessible."}

    # Create a temporary file on the host to store the report
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as report_file_obj:
        host_report_path = Path(report_file_obj.name)

    container_report_path = "/tmp/test_report.json"
    final_command = command.replace("{report_file}", container_report_path)

    # The project directory will be mounted at /app inside the container
    # The WORKDIR in the Dockerfile is /app
    volume_mount = {str(repo_root.resolve()): {'bind': '/app', 'mode': 'rw'}}

    container = None
    try:
        logger.info(f"Running command in container: {final_command}")
        container = client.containers.run(
            TEST_RUNNER_IMAGE,
            command=final_command,
            volumes=volume_mount,
            working_dir="/app",
            detach=True,
        )

        # Wait for the container to finish, with a timeout
        result = container.wait(timeout=300) # 5-minute timeout
        exit_code = result.get("StatusCode", 1)

        # Retrieve the report file from the container
        try:
            bits, stat = container.get_archive(container_report_path)
            # The bits is a tarball stream, we need to extract the file content
            import tarfile
            import io

            with tarfile.open(fileobj=io.BytesIO(b"".join(bits))) as tar:
                report_content = tar.extractfile(tar.getmembers()[0]).read().decode('utf-8')

            report_data = json.loads(report_content)
            report_data["exit_code"] = exit_code
            return report_data

        except docker.errors.NotFound:
             # This happens if the test command failed before creating the report
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            return {
                "error": "Test report file not generated inside the container.",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }

    except docker.errors.ContainerError as e:
        logger.error(f"Container execution failed: {e}")
        return {"error": "Container execution failed.", "details": str(e)}
    except Exception as e:
        logger.error(f"An unexpected error occurred during containerized test run: {e}", exc_info=True)
        return {"error": "An unexpected error occurred."}
    finally:
        if container:
            container.remove(force=True)
        if host_report_path.exists():
            host_report_path.unlink()
