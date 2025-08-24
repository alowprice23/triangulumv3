import logging
from pathlib import Path
import sys
import json
import argparse

# Add project root to the Python path to allow importing from agents, etc.
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.coordinator import Coordinator

# Configure logger for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_all_benchmarks(provider: str, model: str):
    """
    Scans the benchmarks directory and runs the Coordinator for each benchmark.
    """
    benchmarks_dir = project_root / "benchmarks"
    if not benchmarks_dir.is_dir():
        logger.error(f"Benchmarks directory not found at: {benchmarks_dir}")
        return

    logger.info(f"--- Starting Automated Benchmark Run (Provider: {provider}, Model: {model}) ---")

    benchmark_folders = sorted([f for f in benchmarks_dir.iterdir() if f.is_dir()])
    total_benchmarks = len(benchmark_folders)

    for i, benchmark_path in enumerate(benchmark_folders):
        logger.info(f"\n--- Running Benchmark {i+1}/{total_benchmarks}: {benchmark_path.name} ---")

        description_path = benchmark_path / "description.txt"
        if not description_path.is_file():
            logger.warning(f"Skipping benchmark {benchmark_path.name}: description.txt not found.")
            continue

        bug_description = description_path.read_text().strip()

        # Install npm dependencies if package.json exists
        if (benchmark_path / "package.json").is_file():
            logger.info("Found package.json, running npm install...")
            try:
                import subprocess
                subprocess.run(["npm", "install"], cwd=benchmark_path, check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"npm install failed for {benchmark_path.name}: {e}")
                continue

        try:
            # Each benchmark is a self-contained project, so the repo_root is the
            # path to the benchmark itself.
            coordinator = Coordinator(
                repo_root=benchmark_path,
                llm_provider=provider,
                llm_model=model,
                interactive_mode=False
            )

            # Run the debugging cycle. The Coordinator will handle the performance logging.
            result = coordinator.run_debugging_cycle(bug_description)

            logger.info(f"--- Benchmark Result for {benchmark_path.name} ---")
            logger.info(f"Final Status: {result.get('status')}")
            if result.get('status') == 'failed':
                logger.warning(f"Reason: {result.get('reason')}")

        except Exception as e:
            logger.error(f"An unexpected error occurred while running benchmark {benchmark_path.name}: {e}", exc_info=True)

    logger.info("\n--- Automated Benchmark Run Finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Triangulum benchmarks.")
    parser.add_argument(
        "--provider",
        type=str,
        default="ollama",
        help="The LLM provider to use (e.g., 'ollama', 'openai')."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="The specific model to use for the selected provider."
    )
    args = parser.parse_args()

    run_all_benchmarks(args.provider, args.model)
