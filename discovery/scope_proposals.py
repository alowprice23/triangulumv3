import networkx as nx
from pathlib import Path
import os
from typing import List, Dict, Any, Set

from discovery.family_tree import get_family_tree
from entropy.estimator import estimate_h0_from_loc

def _count_loc(repo_root: Path, file_paths: Set[str]) -> int:
    """Counts the total lines of code for a given set of files."""
    total_loc = 0
    for file_path_str in file_paths:
        try:
            with open(repo_root / file_path_str, 'r', encoding='utf-8') as f:
                total_loc += len(f.readlines())
        except (IOError, UnicodeDecodeError):
            # Ignore files that can't be read
            pass
    return total_loc

def propose_scopes(
    graph: nx.DiGraph,
    all_files: List[str],
    target: str,
    repo_root: Path
) -> List[Dict[str, Any]]:
    """
    Proposes different debugging scopes based on a target file or directory.

    Args:
        graph: The dependency graph of the project.
        all_files: A list of all files in the project.
        target: The target file or directory for debugging.
        repo_root: The root path of the repository.

    Returns:
        A list of scope proposals, where each proposal is a dictionary
        containing the name, files, and estimated entropy (H₀).
    """
    proposals = []
    target_path_full = repo_root / target

    # 1. Surgical Scope (if target is a file)
    if target_path_full.is_file() and target in all_files:
        surgical_files = get_family_tree(graph, target)
        if surgical_files:
            loc = _count_loc(repo_root, surgical_files)
            h0 = estimate_h0_from_loc(loc)
            proposals.append({
                "name": f"surgical_scope_for_{target_path_full.name}",
                "files": sorted(list(surgical_files)),
                "tests": [], # Test mapping is not implemented yet
                "entropy_H0": h0
            })

    # 2. Component Scope (if target is a directory)
    if target_path_full.is_dir():
        component_files = {
            f for f in all_files if f.startswith(target)
        }
        if component_files:
            loc = _count_loc(repo_root, component_files)
            h0 = estimate_h0_from_loc(loc)
            proposals.append({
                "name": f"component_scope_for_{target_path_full.name}",
                "files": sorted(list(component_files)),
                "tests": [],
                "entropy_H0": h0
            })

    # 3. Repo-wide Scope
    repo_files = set(all_files)
    loc = _count_loc(repo_root, repo_files)
    h0 = estimate_h0_from_loc(loc)
    proposals.append({
        "name": "repo-wide",
        "files": sorted(list(repo_files)),
        "tests": [],
        "entropy_H0": h0
    })

    return proposals
