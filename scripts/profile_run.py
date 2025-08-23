import cProfile
import pstats
import io
import logging
from pathlib import Path
import os
import shutil

# Configure logger to print to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# This is a bit of a hack to make sure the script can find the other modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
from agents.coordinator import Coordinator

def setup_test_repo():
    """Sets up a temporary buggy project for profiling."""
    repo_root = Path("temp_profiling_project")
    if repo_root.exists():
        shutil.rmtree(repo_root)

    (repo_root / "tests").mkdir(parents=True)
    (repo_root / "__init__.py").touch()
    (repo_root / "tests/__init__.py").touch()
    (repo_root / "math_ops.py").write_text("# Buggy file\ndef add(a, b):\n    return a + b + 1")
    (repo_root / "tests/test_math_ops.py").write_text("from math_ops import add\ndef test_add():\n    assert add(2, 2) == 4")

    return repo_root

def run_for_profiling():
    """The function that will be profiled."""
    repo_path = setup_test_repo()

    # We patch dependencies to simulate a full, successful run without external calls.
    with patch('agents.llm_config.LLMConfig.get_client') as mock_get_client, \
         patch('tooling.test_runner.run_tests') as mock_run_tests:

        # Mock LLM
        mock_llm_client = MagicMock()
        mock_llm_client.get_completion.return_value = "```python\ndef add(a, b):\n    return a + b\n```"
        mock_get_client.return_value = mock_llm_client

        # Mock test runner to simulate (fail -> pass) cycle
        failing_report = {
            "summary": {"failed": 1},
            "tests": [{"outcome": "failed", "nodeid": "tests/test_math_ops.py::test_add"}]
        }
        passing_report = {
            "summary": {"failed": 0},
            "tests": [{"outcome": "passed", "nodeid": "tests/test_math_ops.py::test_add"}]
        }
        # Observer runs once, Verifier runs twice
        mock_run_tests.side_effect = [failing_report, failing_report, passing_report]

        try:
            coordinator = Coordinator(repo_root=repo_path)
            coordinator.run_debugging_cycle(
                bug_description="The add function is returning the wrong sum."
            )
        finally:
            shutil.rmtree(repo_path)


def main():
    """Main function to run the profiler and print results."""
    logger.info("Starting profiler...")

    profiler = cProfile.Profile()
    profiler.enable()

    run_for_profiling()

    profiler.disable()

    logger.info("\n--- Profiling Results ---")
    s = io.StringIO()
    # Sort stats by cumulative time
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20) # Print the top 20 offenders

    # The output of pstats is already formatted, so we print it directly.
    # Using a logger here would add extra formatting.
    print(s.getvalue())

if __name__ == "__main__":
    main()
