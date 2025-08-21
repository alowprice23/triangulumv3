from typing import List, Dict, Any

from kb.patch_motif_library import PatchMotifLibrary

class Memory:
    """
    The Memory module provides the agents with the ability to learn from
    past bug fixes by interacting with the Knowledge Base.
    """
    def __init__(self):
        self.patch_library = PatchMotifLibrary()

    def add_successful_fix(
        self,
        patch_content: str,
        source_file: str,
        error_log: str
    ):
        """
        Stores the details of a successful fix in the knowledge base.

        Args:
            patch_content: The diff of the successful patch.
            source_file: The file that was patched.
            error_log: The original error log of the bug.
        """
        self.patch_library.add_motif(
            patch_content=patch_content,
            source_file=source_file,
            error_log=error_log
        )

    def find_similar_fixes(
        self,
        error_log: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Finds fixes for bugs that are similar to the current one.

        Args:
            error_log: The error log of the current bug.
            file_path: The path to the file suspected to contain the current bug.

        Returns:
            A list of similar past fixes.
        """
        return self.patch_library.find_similar_motifs(
            error_log=error_log,
            file_path=file_path
        )
