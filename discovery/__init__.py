from pathlib import Path
from typing import Dict, Any

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from discovery.scope_proposals import propose_scopes
from discovery.manifest import generate_manifest
from discovery.repo_scanner import scan_repo
from discovery.ignore_rules import IgnoreRules

def run_discovery(repo_path: str, target: str = None) -> Dict[str, Any]:
    """
    Runs the full discovery process on a given repository path.

    Args:
        repo_path: The path to the repository.
        target: An optional specific file or directory to focus on for scope proposals.

    Returns:
        The generated project manifest as a dictionary.
    """
    repo_root = Path(repo_path).resolve()

    # Initialize ignore rules and scan the repository
    ignore_rules = IgnoreRules(repo_root)
    # scan_repo returns Path objects, we need relative strings for the rest of the system
    all_files_paths = scan_repo(repo_root, ignore_rules)
    all_files = [str(p.relative_to(repo_root)) for p in all_files_paths]

    py_files = [f for f in all_files if f.endswith(".py")]

    symbol_index = build_symbol_index(repo_root, py_files)
    graph = build_dependency_graph(symbol_index, py_files)

    scope_target = target if target else "."
    proposals = propose_scopes(graph, all_files, scope_target, repo_root)

    manifest = generate_manifest(repo_root, all_files, graph, proposals)

    return manifest
