from pathlib import Path
from typing import List, Optional

class PythonAdapter:
    """
    Adapter for handling Python-specific project conventions.
    """
    def map_source_to_test(self, source_file: str, all_test_files: List[str]) -> Optional[str]:
        """
        Maps a Python source file to its corresponding test file.

        This uses a simple heuristic based on common project layouts.
        e.g., 'my_app/logic.py' -> 'tests/test_logic.py'

        Args:
            source_file: The relative path to the source file.
            all_test_files: A list of all test files found in the project.

        Returns:
            The relative path to the corresponding test file, or None if not found.
        """
        p = Path(source_file)

        # Try a direct mapping, e.g., 'app/module.py' -> 'tests/test_module.py'
        test_filename = f"test_{p.stem}.py"

        # Look for this test file in common test locations
        # 1. In a parallel 'tests' directory
        possible_test_path = Path("tests") / p.parent / test_filename
        if str(possible_test_path) in all_test_files:
            return str(possible_test_path)

        # 2. In a root 'tests' directory
        possible_test_path_root = Path("tests") / test_filename
        if str(possible_test_path_root) in all_test_files:
            return str(possible_test_path_root)

        # Add more heuristics here in the future

        return None

    def get_test_command(self, test_path: str) -> List[str]:
        """
        Returns the command to run a specific pytest test.
        """
        return ["pytest", test_path]
