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
    for file_str in scope_files:
        total_loc += _count_lines_of_code(repo_root / file_str)

    if total_loc <= 0:
        return 1.0

    h0 = math.log2(total_loc)
    print(f"Entropy Estimator: Calculated H₀ = {h0:.2f} from {total_loc} LOC in {len(scope_files)} files.")
    return h0

# The functions below can be used for plan costing, which is the next step.
def estimate_g_from_patch_size(patch_content: str, total_loc_in_scope: int) -> float:
    """
    Estimates information gain (g) based on the size of the patch relative
    to the scope's total lines of code. A larger, more impactful patch
    provides more information.
    """
    if total_loc_in_scope == 0:
        return 0.0

    # Simple heuristic: number of changed lines / total lines
    # We add 1 to avoid log(0) for empty patches
    changed_lines = len(patch_content.splitlines()) + 1

    # Information gain is proportional to the log of the ratio of total lines to changed lines.
    # This means a smaller change yields less information.
    g = math.log2(total_loc_in_scope / changed_lines)
    return max(0.1, g) # Ensure a minimum information gain to prevent infinite loops

def calculate_n_star(h0: float, g: float) -> int:
    """
    Calculates the expected number of iterations (N*) to solve a bug.
    """
    if g <= 0:
        # Fallback to a default number of attempts if gain is zero or negative
        return 3
    # N_star must be at least 3 to allow for the "fail first, then succeed" cycle.
    return max(3, math.ceil(h0 / g))
