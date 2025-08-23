import math
from pathlib import Path
from typing import List, Set
import networkx as nx

def estimate_h0_from_loc(lines_of_code: int) -> float:
    """
    Estimates the initial entropy (H₀) of a bug based on the lines of code.
    This is a simple heuristic where the search space is proportional to the code size.
    """
    if lines_of_code <= 0:
        return 0.0
    return math.log2(lines_of_code)

def _count_lines_of_code(file_path: Path) -> int:
    """Counts the number of lines in a text file."""
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            return len(f.readlines())
    except Exception:
        return 0

def estimate_initial_entropy(
    failing_test_paths: List[str],
    dep_graph: nx.DiGraph,
    repo_root: Path
) -> float:
    """
    Estimates the initial entropy (H₀) of a bug based on the lines of code
    in the relevant scope (failing tests, their source files, and neighbors).

    Args:
        failing_test_paths: A list of paths to the failing test files.
        dep_graph: The dependency graph of the repository.
        repo_root: The root directory of the repository.

    Returns:
        The estimated initial entropy H₀.
    """
    if not failing_test_paths:
        return 1.0 # Default entropy if no specific test fails

    scope_files: Set[str] = set()

    for test_path_str in failing_test_paths:
        scope_files.add(test_path_str)

        # Heuristic to find the source file from the test file
        test_file_path = Path(test_path_str.split("::")[0])
        source_file_str = str(test_file_path).replace("tests/test_", "src/")
        if dep_graph.has_node(source_file_str):
            scope_files.add(source_file_str)
            # Add all direct dependencies and dependents to the scope
            neighbors = nx.all_neighbors(dep_graph, source_file_str)
            scope_files.update(neighbors)

    total_loc = 0
    total_degree = 0
    for file_str in scope_files:
        total_loc += _count_lines_of_code(repo_root / file_str)
        if dep_graph.has_node(file_str):
            total_degree += dep_graph.degree(file_str)

    avg_degree = (total_degree / len(scope_files)) if scope_files else 0

    # The complexity is a function of both lines of code and connectivity
    complexity_metric = total_loc * (1 + avg_degree)

    if complexity_metric <= 0:
        return 1.0

    h0 = math.log2(complexity_metric)
    print(f"Entropy Estimator: Calculated H₀ = {h0:.2f} from {total_loc} LOC, {len(scope_files)} files, and avg degree {avg_degree:.2f}.")
    return h0

import difflib

# The functions below can be used for plan costing, which is the next step.
def estimate_g_from_patch(original_content: str, patch_content: str) -> float:
    """
    Estimates information gain (g) based on the significance of the change
    introduced by a patch, using a diff ratio.

    Args:
        original_content: The original content of the file.
        patch_content: The content of the file after the patch.

    Returns:
        The estimated information gain (g).
    """
    if not original_content:
        return 1.0 # If the file was created, this is significant gain.

    # Use difflib to get a measure of the change. ratio() returns a measure
    # of the sequences' similarity (0=totally different, 1=identical).
    # We want information gain, so we are interested in the difference.
    similarity = difflib.SequenceMatcher(None, original_content, patch_content).ratio()

    # Information gain is inversely proportional to similarity.
    # If similarity is 1.0 (no change), gain is 0.
    # If similarity is 0.0 (total change), gain is high.
    # We use a simple formula and add a small constant to avoid log(0).
    information_gain = math.log2(1 / (similarity + 0.001) - 0.99)

    return max(0.1, information_gain) # Ensure a minimum gain.

def calculate_n_star(h0: float, g: float) -> int:
    """
    Calculates the expected number of iterations (N*) to solve a bug.
    """
    if g <= 0:
        # Fallback to a default number of attempts if gain is zero or negative
        return 3
    # N_star must be at least 3 to allow for the "fail first, then succeed" cycle.
    return max(3, math.ceil(h0 / g))
