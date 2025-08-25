"""
A script to run a simulation of the Triangulum supervisor for a fixed
number of ticks and generate a reference trace of its state.
"""
import random
import json
import time
from pathlib import Path

# This is a standalone script, so we need to adjust the Python path
# to import modules from the main application.
import sys
sys.path.append(str(Path(__file__).parent.parent))

from runtime.supervisor import Supervisor

# --- Simulation Parameters ---
SIMULATION_TICKS = 60
BUG_SUBMISSION_PROBABILITY = 0.3 # 30% chance of a new bug each tick
OUTPUT_TRACE_FILE = "simulation_trace.jsonl"

def run_simulation():
    """
    Initializes a supervisor and runs it for a fixed number of ticks,
    simulating bug submissions and recording state at each tick.
    """
    print("--- Starting Triangulum Simulation ---")

    # Initialize a supervisor. We can run it without a real repo_root
    # for this simulation, as we are not actually executing agents.
    supervisor = Supervisor(repo_root=Path("buggy_project"))

    trace_data = []

    for tick in range(SIMULATION_TICKS):
        print(f"\n--- Tick {tick+1}/{SIMULATION_TICKS} ---")

        # Simulate new bug submissions
        if random.random() < BUG_SUBMISSION_PROBABILITY:
            severity = random.randint(1, 10)
            description = f"Simulated bug at tick {tick+1}"
            supervisor.submit_bug(description, severity)

        # Run one tick of the supervisor loop
        supervisor.tick()

        # Capture state for the trace
        current_state = {
            "tick": tick + 1,
            "timestamp": time.time(),
            "queued_tickets": len(supervisor.scheduler),
            "active_sessions": supervisor.executor.get_active_session_count(),
        }
        trace_data.append(current_state)

        print(f"State: {current_state}")

        # In a real simulation, we might not want to sleep, but for this
        # simple script, it makes the output more readable.
        time.sleep(0.1)

    # Save the trace data to a JSONL file
    with open(OUTPUT_TRACE_FILE, "w") as f:
        for entry in trace_data:
            f.write(json.dumps(entry) + "\\n")

    print(f"\n--- Simulation Complete ---")
    print(f"Trace data saved to {OUTPUT_TRACE_FILE}")

if __name__ == "__main__":
    run_simulation()
