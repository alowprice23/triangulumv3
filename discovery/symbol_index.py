import ast
from pathlib import Path
import click

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
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    prefix = '.' * node.level
                    if node.module:
                        imports.add(prefix + node.module)
                    else:
                        for alias in node.names:
                            imports.add(prefix + alias.name)
                elif node.module:
                    for alias in node.names:
                         if alias.name != '*':
                            imports.add(f"{node.module}.{alias.name}")

    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        # Print warnings to stderr so they don't pollute stdout
        click.echo(f"Warning: Could not parse {file_path}: {e}", err=True)
    return sorted(list(imports))

def build_symbol_index(repo_root: Path, files: list[str]) -> dict:
    """
    Builds a simplified symbol index for the given files, focusing only on imports.
    """
    index = {}
    for file_str in files:
        file_path = repo_root / file_str
        if file_path.suffix == ".py":
            imports = _get_imports(file_path)
            if imports:
                index[file_str] = {"imports": imports}
    return index
