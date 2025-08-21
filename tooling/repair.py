import networkx as nx
from typing import List, Dict, Set

class RepairTool:
    """
    A tool for analyzing and applying patches in a dependency-aware manner.
    """
    def __init__(self, dependency_graph: nx.DiGraph):
        if not isinstance(dependency_graph, nx.DiGraph):
            raise TypeError("dependency_graph must be a networkx.DiGraph")
        self.graph = dependency_graph

    def analyze_ripple_effect(self, patched_files: List[str]) -> Dict[str, List[str]]:
        """
        Analyzes the potential downstream impact of patching a set of files.
        Downstream dependencies are files that import the patched file (predecessors).

        Args:
            patched_files: A list of file paths that have been patched.

        Returns:
            A dictionary where keys are the patched files and values are lists
            of downstream files that might be affected.
        """
        ripple_effects = {}
        for file_path in patched_files:
            if self.graph.has_node(file_path):
                # In our graph (A -> B means A imports B), a change in B affects A.
                # Therefore, we need to find the predecessors of the patched file.
                # We use ancestors to find all files that depend on it, recursively.
                affected_files = nx.ancestors(self.graph, file_path)
                ripple_effects[file_path] = sorted(list(affected_files))
            else:
                ripple_effects[file_path] = []

        return ripple_effects
