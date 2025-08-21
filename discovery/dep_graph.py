import networkx as nx
from pathlib import Path
import os

def _resolve_import_to_path(module_name: str, all_files_set: set[str], source_file: str) -> str | None:
    """
    Resolves an import module name to a file path within the project.
    This is a simplified resolver. A real implementation would need to handle
    sys.path, .pth files, C extensions, etc.
    """
    # Attempt to resolve absolute imports
    # e.g., "my_app.components.utils" -> "my_app/components/utils"
    module_path = Path(module_name.replace('.', os.sep))

    # Check for a direct .py file match
    possible_path1 = module_path.with_suffix(".py")
    if str(possible_path1) in all_files_set:
        return str(possible_path1)

    # Check for a package match (__init__.py)
    possible_path2 = module_path / "__init__.py"
    if str(possible_path2) in all_files_set:
        return str(possible_path2)

    # Attempt to resolve relative imports
    if module_name.startswith('.'):
        level = 0
        for char in module_name:
            if char == '.':
                level += 1
            else:
                break

        module_name_without_dots = module_name[level:]

        # Relative path needs a base
        if not source_file:
            return None

        base_path = Path(source_file).parent
        for _ in range(level - 1):
            base_path = base_path.parent

        if module_name_without_dots:
            relative_module_path = Path(module_name_without_dots.replace('.', os.sep))

            # Check for .py file
            possible_relative_path1 = base_path / relative_module_path.with_suffix(".py")
            if str(possible_relative_path1) in all_files_set:
                return str(possible_relative_path1)

            # Check for package
            possible_relative_path2 = base_path / relative_module_path / "__init__.py"
            if str(possible_relative_path2) in all_files_set:
                return str(possible_relative_path2)
        else: # from . import foo
             # This case implies the module is in the same directory
             pass


    return None


def build_dependency_graph(symbol_index: dict, all_files: list[str]) -> nx.DiGraph:
    """
    Constructs a dependency graph from a symbol index.

    Args:
        symbol_index: A dictionary from file paths to their imports.
                      (Output of `discovery.symbol_index.build_symbol_index`)
        all_files: A list of all file paths in the repository.

    Returns:
        A networkx.DiGraph representing the dependency graph.
    """
    graph = nx.DiGraph()
    all_files_set = set(all_files)

    # Add all python files as nodes
    for file_path in all_files:
        if file_path.endswith(".py"):
            graph.add_node(file_path)

    # Add edges based on imports
    for source_file, data in symbol_index.items():
        if not graph.has_node(source_file):
            continue

        imports = data.get("imports", [])
        for module_name in imports:
            # Attempt to resolve the imported module to a file in the project
            target_file = _resolve_import_to_path(module_name, all_files_set, source_file)

            if target_file and target_file in all_files_set:
                # Add an edge from the file that imports to the file that is imported
                if source_file != target_file: # Avoid self-loops for now
                    graph.add_edge(source_file, target_file)

    return graph
