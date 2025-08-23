import pathspec
from pathlib import Path
from typing import List, Set

DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "build/",
    "dist/",
    "*.egg-info/",
    "node_modules/",
]

from typing import Optional

class IgnoreRules:
    """
    Manages ignore rules from .gitignore, .triangulumignore, and default patterns,
    using the `pathspec` library for robust .gitignore-style matching.
    """
    def __init__(self, additional_patterns: List[str] = [], project_root: Optional[Path] = None):
        self.project_root = project_root
        self.patterns: Set[str] = set(DEFAULT_IGNORE_PATTERNS)
        self.patterns.update(additional_patterns)

        if self.project_root:
            self._load_ignore_files()

        self.spec = pathspec.PathSpec.from_lines(
            pathspec.GitIgnorePattern, self.get_patterns()
        )

    def _load_ignore_files(self):
        """Loads ignore patterns from .gitignore and .triangulumignore."""
        for ignore_file in [".gitignore", ".triangulumignore"]:
            if self.project_root:
                ignore_path = self.project_root / ignore_file
                if ignore_path.is_file():
                    with open(ignore_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                self.patterns.add(line)

    def is_ignored(self, path: Path) -> bool:
        """
        Checks if a given path should be ignored.
        The path should be relative to the project root.
        """
        return self.spec.match_file(str(path))

    def get_patterns(self) -> List[str]:
        """Returns the list of all ignore patterns."""
        return sorted(list(self.patterns))

    def __repr__(self) -> str:
        return f"IgnoreRules(patterns={len(self.patterns)})"
