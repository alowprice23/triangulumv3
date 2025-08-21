# discovery/symbol_index.py

import ast
from pathlib import Path

def _get_imports(file_path: Path) -> list[str]:
    """
    Extracts a list of imported module names from a Python file.
    Uses AST parsing to be accurate.
    """
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # e.g., import my.module
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                # e.g., from pathlib import Path -> "pathlib"
                # e.g., from . import base -> ".base"
                if node.level > 0:
                    prefix = '.' * node.level
                    if node.module:
                        imports.add(prefix + node.module)
                    else: # from . import foo, bar
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                elif node.module:
                    # from my.module import something -> "my.module.something"
                    # This is a simplification. A full implementation would need
                    # to handle wildcards, etc.
                    for alias in node.names:
                         if alias.name != '*':
                            imports.add(f"{node.module}.{alias.name}")

    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        # Ignore files that can't be parsed
        print(f"Warning: Could not parse {file_path}: {e}")
    return sorted(list(imports))

def build_symbol_index(repo_root: Path, files: list[str]) -> dict:
    """
    Builds a simplified symbol index for the given files, focusing only on imports.
    This is a prerequisite for constructing the dependency graph.

    The schema is:
    {
        "path/to/file.py": {
            "imports": ["module1", "module2"]
        },
        ...
    }

    Args:
        repo_root: The root path of the repository.
        files: A list of file paths relative to the repo root.

    Returns:
        A dictionary representing the symbol index.
    """
    index = {}
    for file_str in files:
        file_path = repo_root / file_str
        if file_path.suffix == ".py":
            imports = _get_imports(file_path)
            if imports:
                index[file_str] = {"imports": imports}
    return index
