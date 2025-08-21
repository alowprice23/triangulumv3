from pathlib import Path
from typing import Dict, Any

from discovery.symbol_index import build_symbol_index
from discovery.dep_graph import build_dependency_graph
from discovery.scope_proposals import propose_scopes
from discovery.manifest import generate_manifest
from discovery.repo_scanner import scan_repo
from discovery.ignore_rules import IgnoreRules
from discovery.test_locator import SourceTestMapper

def run_discovery(repo_path: str, target: str = None) -> Dict[str, Any]:
    """
    Runs the full discovery process on a given repository path.
    """
    repo_root = Path(repo_path).resolve()

    ignore_rules = IgnoreRules(repo_root)
    all_files_paths = scan_repo(repo_root, ignore_rules)
    all_files = [str(p.relative_to(repo_root)) for p in all_files_paths]

    py_files = [f for f in all_files if f.endswith(".py")]

    symbol_index = build_symbol_index(repo_root, py_files)
    graph = build_dependency_graph(symbol_index, py_files)

    # Locate tests using the new mapper
    test_mapper = SourceTestMapper()
    test_mapping = test_mapper.locate_tests(all_files, repo_root)

    scope_target = target if target else "."
    # Pass the test mapping to scope proposals so it can be included in the manifest later
    proposals = propose_scopes(graph, all_files, scope_target, repo_root)

    # Pass the test mapping to the manifest generator
    manifest = generate_manifest(repo_root, all_files, graph, proposals, test_mapping)

    return manifest
