import unittest
import math
from pathlib import Path
import tempfile
import shutil
import networkx as nx

from entropy.estimator import (
    estimate_initial_entropy,
    estimate_g_from_patch,
    calculate_n_star,
    _count_lines_of_code,
    estimate_h0_from_loc,
)

class TestEntropyEstimator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_estimate_initial_entropy(self):
        """Tests the H₀ estimation from a scope of files."""
        # Create dummy files and a dependency graph
        (self.repo_root / "src").mkdir()
        (self.repo_root / "tests").mkdir()

        # Files in scope
        (self.repo_root / "src" / "main.py").write_text("line\n" * 100) # 100 lines
        (self.repo_root / "src" / "utils.py").write_text("line\n" * 50) # 50 lines
        (self.repo_root / "tests" / "test_main.py").write_text("line\n" * 30) # 30 lines

        # File out of scope
        (self.repo_root / "src" / "other.py").write_text("line\n" * 1000)

        graph = nx.DiGraph()
        graph.add_node("src/main.py")
        graph.add_node("src/utils.py")
        graph.add_node("tests/test_main.py")
        graph.add_edge("src/main.py", "src/utils.py") # main depends on utils
        graph.add_edge("tests/test_main.py", "src/main.py") # test depends on main

        # Total LOC = 100 + 50 + 30 = 180
        # Avg degree = (degree(main) + degree(utils) + degree(test)) / 3 = (2 + 1 + 1) / 3 = 1.333
        # Complexity = 180 * (1 + 1.333) = 420
        expected_h0 = math.log2(180 * (1 + 4/3))

        h0 = estimate_initial_entropy(
            failing_test_paths=["tests/test_main.py"],
            dep_graph=graph,
            repo_root=self.repo_root
        )
        self.assertAlmostEqual(h0, expected_h0, places=5)

    def test_estimate_g_from_patch(self):
        """Tests the information gain (g) estimation from a diff."""
        original = "line1\nline2\nline3"
        modified = "line1\nline_two\nline3"
        g = estimate_g_from_patch(original, modified)
        self.assertGreaterEqual(g, 0.1) # Check that it returns a valid gain

    def test_calculate_n_star(self):
        """Tests the N* calculation."""
        self.assertEqual(calculate_n_star(10.0, 1.0), 10)
        self.assertEqual(calculate_n_star(10.0, 2.0), 5)
        self.assertEqual(calculate_n_star(10.5, 1.0), 11)
        self.assertEqual(calculate_n_star(10.0, 0.0), 3) # Fallback
        self.assertEqual(calculate_n_star(10.0, -1.0), 3) # Fallback

if __name__ == '__main__':
    unittest.main()
