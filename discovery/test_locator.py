from typing import List, Dict, Optional
from pathlib import Path

from adapters.python import PythonAdapter
from adapters.node import NodeAdapter
from discovery.language_probe import probe_language

class SourceTestMapper:
    """
    Locates test files and maps them to their corresponding source files
    using language-specific adapters.
    """
    def __init__(self):
        # A registry of available language adapters
        self.adapters = {
            "Python": PythonAdapter(),
            "JavaScript": NodeAdapter(),
            "TypeScript": NodeAdapter(),
        }

    def _is_test_file(self, file_path: str) -> bool:
        """A simple heuristic to identify test files."""
        p = Path(file_path)
        return "test" in p.name.lower() or "spec" in p.name.lower()

    def locate_tests(
        self,
        all_files: List[str],
        repo_root: Path
    ) -> Dict[str, Optional[str]]:
        """
        Creates a mapping from source files to their test files.

        Args:
            all_files: A list of all file paths in the repository.
            repo_root: The root path of the repository.

        Returns:
            A dictionary mapping each source file to its test file, if found.
        """
        all_file_paths = [repo_root / f for f in all_files]
        primary_language = probe_language(all_file_paths)

        adapter = self.adapters.get(primary_language)
        if not adapter:
            print(f"Warning: No suitable test adapter found for language: {primary_language}")
            return {}

        source_files = [f for f in all_files if not self._is_test_file(f)]
        test_files = [f for f in all_files if self._is_test_file(f)]

        mapping = {}
        for source_file in source_files:
            test_file = adapter.map_source_to_test(source_file, test_files)
            if test_file:
                mapping[source_file] = test_file

        return mapping
