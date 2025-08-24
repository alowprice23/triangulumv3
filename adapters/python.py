import ast
from pathlib import Path
from typing import List, Dict, Any
import networkx as nx
import os

from adapters.base_adapter import LanguageAdapter

# --- Helper functions for Python-specific analysis ---

def _get_python_imports(file_path: Path) -> list[str]:
    """
    Extracts a list of imported module names from a Python file.
    """
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0: # Relative import
                    # We construct a resolvable path-like string
                    prefix = '.' * node.level
                    if node.module:
                        imports.add(prefix + node.module)
                    else: # from . import x
                        imports.add(prefix)
                elif node.module: # Absolute import
                    imports.add(node.module)
    except Exception:
        # Ignore files that can't be parsed
        pass
    return sorted(list(imports))

def _resolve_python_import_to_path(module_name: str, all_files_set: set[str], source_file: str) -> str | None:
    """
    Resolves an import module name to a file path within the project.
    """
    # Handle absolute imports (e.g., "my_app.components.utils")
    if not module_name.startswith('.'):
        module_path = Path(module_name.replace('.', os.sep))
        possible_path1 = module_path.with_suffix(".py")
        if str(possible_path1) in all_files_set:
            return str(possible_path1)
        possible_path2 = module_path / "__init__.py"
        if str(possible_path2) in all_files_set:
            return str(possible_path2)
        return None

    # Handle relative imports (e.g., ".utils" or "..models")
    level = 0
    for char in module_name:
        if char == '.': level += 1
        else: break

    base_path = Path(source_file).parent
    for _ in range(level - 1):
        base_path = base_path.parent

    module_name_without_dots = module_name[level:]
    if module_name_without_dots:
        relative_module_path = Path(module_name_without_dots.replace('.', os.sep))
        possible_path1 = (base_path / relative_module_path).with_suffix(".py")
        if str(possible_path1) in all_files_set:
            return str(possible_path1)
        possible_path2 = base_path / relative_module_path / "__init__.py"
        if str(possible_path2) in all_files_set:
            return str(possible_path2)
    else: # from . import foo
        possible_path = (base_path).with_suffix(".py")
        if str(possible_path) in all_files_set:
            return str(possible_path)

    return None

# --- Adapter Implementation ---

class PythonAdapter(LanguageAdapter):
    """
    An adapter for analyzing Python codebases.
    """

    def build_symbol_index(self, repo_root: Path, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parses Python files using AST to build a comprehensive symbol index.
        """
        index = {}
        for file_str in file_paths:
            if not file_str.endswith(".py"):
                continue

            file_path = repo_root / file_str
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(file_path))

                symbols = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        start_line = node.lineno
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line

                        # Get the full source segment of the node
                        source_segment = ast.get_source_segment(content, node) or ""

                        symbols.append({
                            "name": node.name,
                            "type": type(node).__name__,
                            "start_line": start_line,
                            "end_line": end_line,
                            "source_code": source_segment,
                            "dependencies": [], # Will be filled in later if needed
                        })
                if symbols:
                    index[file_str] = symbols
            except Exception:
                # Ignore files that can't be parsed
                pass
        return index

    def build_dependency_graph(self, symbol_index: Dict[str, List[Dict[str, Any]]], file_paths: List[str]) -> nx.DiGraph:
        """
        Constructs a dependency graph for Python modules based on imports.
        """
        graph = nx.DiGraph()
        all_files_set = set(file_paths)

        for file_path_str in file_paths:
            if file_path_str.endswith(".py"):
                graph.add_node(file_path_str)

        for source_file_str in file_paths:
            if not source_file_str.endswith(".py"):
                continue

            imports = _get_python_imports(Path(source_file_str))
            for module_name in imports:
                target_file = _resolve_python_import_to_path(module_name, all_files_set, source_file_str)
                if target_file and target_file in all_files_set:
                    if source_file_str != target_file:
                        graph.add_edge(source_file_str, target_file)
        return graph

    def get_test_command(self, test_targets: List[str]) -> str:
        """
        Generates a pytest command that produces a JSON report.
        """
        targets_str = " ".join(test_targets)

        # The {report_file} placeholder will be replaced by the test_runner
        command = (
            f"pytest -p no:cacheprovider --json-report "
            f"--json-report-file={{report_file}} --json-report-summary {targets_str}"
        )
        return command

    def map_source_to_test(self, source_file: str, all_tests: List[str]) -> str | None:
        """
        Maps a Python source file to its corresponding test file.
        """
        source_path = Path(source_file)
        test_file_name = f"test_{source_path.stem}.py"
        for test_path in all_tests:
            if Path(test_path).name == test_file_name:
                return test_path
        return None
