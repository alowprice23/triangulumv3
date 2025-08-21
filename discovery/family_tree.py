import networkx as nx
from typing import Set

def get_family_tree(graph: nx.DiGraph, target_file: str) -> Set[str]:
    """
    Computes the "family tree" for a given target file from a dependency graph.

    The family tree consists of:
    1. The target file itself.
    2. All upstream dependencies (ancestors): files that the target file depends on,
       recursively.
    3. All downstream dependents (descendants): files that depend on the target file,
       recursively.

    Args:
        graph: A networkx.DiGraph representing the dependency graph.
        target_file: The path of the file to compute the family tree for.

    Returns:
        A set of file paths representing the complete family tree.
        Returns an empty set if the target file is not in the graph.
    """
    if not graph.has_node(target_file):
        return set()

    # Find all upstream dependencies (ancestors)
    try:
        ancestors = nx.ancestors(graph, target_file)
    except nx.NetworkXError:
        ancestors = set()

    # Find all downstream dependents (descendants)
    try:
        descendants = nx.descendants(graph, target_file)
    except nx.NetworkXError:
        descendants = set()

    # The family tree is the union of the target, its ancestors, and its descendants
    family_tree = {target_file}
    family_tree.update(ancestors)
    family_tree.update(descendants)

    return family_tree
