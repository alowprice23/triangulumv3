import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from discovery.ignore_rules import IgnoreRules

class RepoScanner:
    """
    Scans a repository to create a manifest of all non-ignored files,
    using a cache to speed up subsequent scans.
    """
    def __init__(self, ignore_rules: IgnoreRules, cache_path: Optional[Path] = None):
        if not isinstance(ignore_rules, IgnoreRules):
            raise TypeError("ignore_rules must be an instance of IgnoreRules")
        self.ignore_rules = ignore_rules
        self.cache_path = cache_path
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Loads the file manifest cache from disk if it exists."""
        if self.cache_path and self.cache_path.is_file():
            try:
                with self.cache_path.open("r") as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                return {}
        return {}

    def _save_cache(self):
        """Saves the file manifest cache to disk."""
        if self.cache_path:
            try:
                with self.cache_path.open("w") as f:
                    json.dump(self.cache, f)
            except IOError:
                pass # Fail silently if we can't write the cache

    def _hash_file(self, file_path: Path) -> str:
        """Computes the SHA256 hash of a file's content."""
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def scan(self, project_root: Path) -> List[Dict[str, Any]]:
        """
        Scans a repository and returns a manifest of files. Uses a cache
        to avoid re-hashing unchanged files.
        """
        if not project_root.is_dir():
            raise ValueError("Project root must be a directory.")

        manifest = []
        current_files = set()

        for path in project_root.rglob("*"):
            if path.is_file():
                relative_path_str = str(path.relative_to(project_root))
                current_files.add(relative_path_str)

                if not self.ignore_rules.is_ignored(Path(relative_path_str)):
                    try:
                        mtime = path.stat().st_mtime
                        cached_file = self.cache.get(relative_path_str)

                        if cached_file and cached_file.get("mtime") == mtime:
                            # Use cached data
                            file_info = cached_file
                        else:
                            # File is new or modified, re-hash and update cache
                            file_hash = self._hash_file(path)
                            file_info = {"path": relative_path_str, "hash": file_hash, "mtime": mtime}
                            self.cache[relative_path_str] = file_info

                        manifest.append(file_info)
                    except FileNotFoundError:
                        continue # File might have been deleted during scan

        # Remove files from cache that no longer exist
        deleted_files = set(self.cache.keys()) - current_files
        for file_path in deleted_files:
            del self.cache[file_path]

        self._save_cache()
        return manifest
