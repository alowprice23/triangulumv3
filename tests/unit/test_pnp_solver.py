import unittest
from entropy.pnp_solver import PnPSolver

class TestPnpSolver(unittest.TestCase):

    def setUp(self):
        """Create a new solver for each test."""
        self.solver = PnPSolver()

    def test_solve_simple_scenario(self):
        """Test a basic solvable scenario."""
        scope_files = ["file_a.py", "file_b.py", "file_c.py"]
        tests = [
            # Test 1 covers A and B, and passes. So, A and B must be correct.
            {"name": "test_1", "is_passing": True, "covers_files": ["file_a.py", "file_b.py"]},
            # Test 2 covers B and C, and fails. Since we know B is correct, C must be buggy.
            {"name": "test_2", "is_passing": False, "covers_files": ["file_b.py", "file_c.py"]},
        ]

        result = self.solver.solve(scope_files, tests)

        self.assertEqual(result["status"], "solved")
        self.assertIn("file_c.py", result["likely_buggy_files"])
        self.assertNotIn("file_a.py", result["likely_buggy_files"])
        self.assertNotIn("file_b.py", result["likely_buggy_files"])

    def test_solve_unsolvable_scenario(self):
        """Test a contradictory (UNSAT) scenario."""
        scope_files = ["file_a.py"]
        tests = [
            # Test 1 covers A and passes. So, A must be correct.
            {"name": "test_1", "is_passing": True, "covers_files": ["file_a.py"]},
            # Test 2 also covers A but fails. So, A must be buggy.
            # This is a contradiction.
            {"name": "test_2", "is_passing": False, "covers_files": ["file_a.py"]},
        ]

        result = self.solver.solve(scope_files, tests)
        self.assertEqual(result["status"], "unsat")

    def test_solve_no_failing_tests(self):
        """Test a scenario with no failing tests."""
        scope_files = ["file_a.py", "file_b.py"]
        tests = [
            {"name": "test_1", "is_passing": True, "covers_files": ["file_a.py"]},
            {"name": "test_2", "is_passing": True, "covers_files": ["file_b.py"]},
        ]

        result = self.solver.solve(scope_files, tests)
        self.assertEqual(result["status"], "solved")
        # With no failing tests, no files should be identified as buggy.
        self.assertEqual(len(result["likely_buggy_files"]), 0)

if __name__ == '__main__':
    unittest.main()
