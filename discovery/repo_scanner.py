import hashlib
from pathlib import Path
from typing import List, Dict, Any

from discovery.ignore_rules import IgnoreRules

class RepoScanner:
    """
    Scans a repository to create a manifest of all non-ignored files.
    """
    def __init__(self, ignore_rules: IgnoreRules):
        if not isinstance(ignore_rules, IgnoreRules):
            raise TypeError("ignore_rules must be an instance of IgnoreRules")
        self.ignore_rules = ignore_rules

    def _hash_file(self, file_path: Path) -> str:
        """Computes the SHA256 hash of a file's content."""
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            buf = f.read(65536) # Read in 64k chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def scan(self, project_root: Path) -> List[Dict[str, Any]]:
        """
        Scans a repository and returns a manifest of files.

        The manifest is a list of dictionaries, where each dictionary
        represents a file and contains its path and content hash.

        Args:
            project_root: The root directory of the repository to scan.

        Returns:
            A list of dictionaries representing the file manifest.
        """
        if not project_root.is_dir():
            raise ValueError("Project root must be a directory.")

        manifest = []
        for path in project_root.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(project_root)
                if not self.ignore_rules.is_ignored(relative_path):
                    file_info = {
                        "path": str(relative_path),
                        "hash": self._hash_file(path)
                    }
                    manifest.append(file_info)

        return manifest
