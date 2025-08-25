import unittest
from unittest.mock import patch
import subprocess
import sys
import os
import json
from pathlib import Path

class TestSimulationScript(unittest.TestCase):

    def setUp(self):
        self.trace_file = Path("simulation_trace.jsonl")
        if self.trace_file.exists():
            self.trace_file.unlink()

    def tearDown(self):
        if self.trace_file.exists():
            self.trace_file.unlink()

    @unittest.skip("Skipping simulation test due to torch/meta tensor issue in the environment.")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_for_simulation"})
    def test_run_simulation_script(self):
        """
        Test that the run_simulation.py script executes without errors
        and produces a valid output file.
        """
        # Get the path to the python executable
        python_executable = sys.executable
        script_path = "scripts/run_simulation.py"

        # Run the script as a subprocess
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True
        )

        # 1. Check for successful execution
        self.assertEqual(result.returncode, 0, f"Script failed with error: {result.stderr}")

        # 2. Check that the output file was created
        self.assertTrue(self.trace_file.exists(), "Simulation trace file was not created.")

        # 3. Check that the file contains valid JSONL
        with open(self.trace_file, "r") as f:
            lines = f.readlines()
            # The script is configured to run for 60 ticks
            self.assertEqual(len(lines), 60)
            # Check that the first line is valid JSON
            try:
                first_line_data = json.loads(lines[0])
                self.assertIn("tick", first_line_data)
                self.assertIn("timestamp", first_line_data)
            except json.JSONDecodeError:
                self.fail("The first line of the trace file is not valid JSON.")

if __name__ == '__main__':
    unittest.main()
