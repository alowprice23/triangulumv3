import unittest
from unittest.mock import patch
import networkx as nx
from pathlib import Path

from tooling.repair import RepairTool

class TestEnhancedTooling(unittest.TestCase):

    def test_repair_tool_ripple_analysis(self):
        """Test the ripple effect analysis of the RepairTool."""
        # Graph: main -> utils -> logger. main -> api
        # A change in logger should affect utils and main.
        graph = nx.DiGraph()
        graph.add_edges_from([
            ("main.py", "utils.py"),
            ("utils.py", "logger.py"),
            ("main.py", "api.py")
        ])

        repair_tool = RepairTool(dependency_graph=graph)

        # 1. Analyze effect of patching logger.py
        effects_logger = repair_tool.analyze_ripple_effect(["logger.py"])
        # Expect to find utils.py and main.py (recursive ancestors)
        self.assertEqual(effects_logger["logger.py"], ["main.py", "utils.py"])

        # 2. Analyze effect of patching utils.py
        effects_utils = repair_tool.analyze_ripple_effect(["utils.py"])
        # Expect to find main.py
        self.assertEqual(effects_utils["utils.py"], ["main.py"])

        # 3. Analyze effect of patching a file with no dependents
        effects_main = repair_tool.analyze_ripple_effect(["main.py"])
        self.assertEqual(effects_main["main.py"], [])


if __name__ == '__main__':
    unittest.main()
