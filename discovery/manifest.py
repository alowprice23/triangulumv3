import json
import hashlib
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any

def _hash_file(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file's content."""
    h = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except IOError:
        return ""

def _hash_graph(graph: nx.DiGraph) -> str:
    """Computes a SHA-256 hash of the graph structure."""
    # node_link_data provides a canonical representation
    graph_data = nx.node_link_data(graph)
    # Sort to ensure consistent hashing
    sorted_graph_string = json.dumps(graph_data, sort_keys=True)
    return hashlib.sha256(sorted_graph_string.encode('utf-8')).hexdigest()

def generate_manifest(
    repo_root: Path,
    all_files: List[str],
    graph: nx.DiGraph,
    proposed_scopes: List[Dict[str, Any]],
    # In a full implementation, we'd also pass test_mappings and language_info
) -> Dict[str, Any]:
    """
    Generates a machine-readable manifest of the project structure.

    Args:
        repo_root: The root path of the repository.
        all_files: A list of all project files.
        graph: The dependency graph.
        proposed_scopes: A list of scope proposals.

    Returns:
        A dictionary representing the project manifest.
    """
    manifest = {
        "version": "1.0",
        "project_root": str(repo_root),
        "files": [],
        "tests": {}, # Placeholder, requires test_locator.py
        "dependency_graph": {},
        "proposed_scopes": proposed_scopes,
    }

    # Populate file list with hashes
    for file_str in all_files:
        manifest["files"].append({
            "path": file_str,
            "language": "unknown", # Placeholder, requires language_probe.py
            "hash": _hash_file(repo_root / file_str),
        })

    # Serialize and hash the dependency graph
    if graph:
        manifest["dependency_graph"] = {
            **nx.node_link_data(graph),
            "hash": _hash_graph(graph),
        }


    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path):
    """Saves the manifest dictionary to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
