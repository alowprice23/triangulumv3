"""
Adapter for handling Node.js (JavaScript/TypeScript) specific project conventions.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx

from adapters.base_adapter import LanguageAdapter

# --- Helper functions for JS/TS analysis ---

def _get_js_imports(file_content: str) -> List[str]:
    """
    Extracts a list of imported module names from a JS/TS file using regex.
    This is a simplified approach and may not cover all edge cases.
    """
    # Regex for: import ... from '...'; OR require('...');
    import_pattern = re.compile(r"import\s+.*\s+from\s+['\"](.*?)['\"];?|require\(['\"](.*?)['\"]\)", re.MULTILINE)
    imports = []
    for match in import_pattern.finditer(file_content):
        # The regex has two capturing groups, one for `import` and one for `require`.
        # One of them will be None for each match.
        path = match.group(1) or match.group(2)
        if path:
            imports.append(path)
    return imports

# --- Adapter Implementation ---

class NodeAdapter(LanguageAdapter):
    """
    An adapter for analyzing JavaScript and TypeScript codebases.
    """

    def map_source_to_test(self, source_file: str, all_tests: List[str]) -> Optional[str]:
        """
        Maps a JS/TS source file to its corresponding test file using heuristics.
        1.  Import-based matching.
        2.  Name-based matching.
        """
        source_path = Path(source_file)

        # 1. Import-based matching
        for test_file in all_tests:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()
                imports = _get_js_imports(content)
                for imp in imports:
                    # This is a simplified resolution logic. A real implementation
                    # would need to handle path aliases, relative paths, etc.
                    if imp.endswith(source_path.stem):
                        return test_file
            except Exception:
                continue

        # 2. Name-based matching
        stem = source_path.stem
        possible_test_names = {f"{stem}.test.js", f"{stem}.spec.js", f"{stem}.test.ts", f"{stem}.spec.ts"}
        for test_file in all_tests:
            if Path(test_file).name in possible_test_names:
                return test_file

        return None

    def get_test_command(self, test_targets: List[str]) -> str:
        """
        Generates a test command for a Node.js project.
        Detects the package manager and uses the appropriate test runner command.
        """
        # This is a simplified detection logic.
        # A real implementation would check for lock files.
        package_manager = "npm" # Default
        if Path("yarn.lock").exists():
            package_manager = "yarn"
        elif Path("pnpm-lock.yaml").exists():
            package_manager = "pnpm"

        targets_str = " ".join(test_targets)
        # Assuming jest or a compatible test runner is configured in package.json script
        return f"{package_manager} test {targets_str}"

    def build_symbol_index(self, repo_root: Path, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Builds a simplified symbol index for JS/TS files using regex.
        This is a heuristic-based approach.
        """
        index = {}
        # Regex for: function name(...), const name = (...) =>, class Name {
        symbol_pattern = re.compile(r"^(?:function\s+(\w+)|const\s+(\w+)\s*=\s*\(|class\s+(\w+))", re.MULTILINE)

        for file_str in file_paths:
            if not (file_str.endswith(".js") or file_str.endswith(".ts")):
                continue

            file_path = repo_root / file_str
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()

                symbols = []
                for match in symbol_pattern.finditer(content):
                    name = match.group(1) or match.group(2) or match.group(3)
                    if name:
                        symbols.append({
                            "name": name,
                            "type": "function" if match.group(1) or match.group(2) else "class",
                            "start_line": content.count('\\n', 0, match.start()) + 1,
                        })
                if symbols:
                    index[file_str] = symbols
            except Exception:
                continue
        return index

    def build_dependency_graph(self, symbol_index: Dict[str, List[Dict[str, Any]]], file_paths: List[str]) -> nx.DiGraph:
        """
        Constructs a dependency graph for JS/TS modules based on imports.
        """
        graph = nx.DiGraph()
        for file_path in file_paths:
            graph.add_node(file_path)

        for source_file in file_paths:
            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    content = f.read()
                imports = _get_js_imports(content)
                for imp in imports:
                    # This resolution is highly simplified.
                    # A real implementation would need a proper resolver.
                    for target_file in file_paths:
                        if imp.endswith(Path(target_file).stem):
                            graph.add_edge(source_file, target_file)
            except Exception:
                continue
        return graph
