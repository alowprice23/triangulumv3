import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any

from kb.vector_db import VectorDBClient

class PatchMotifLibrary:
    """
    Manages a library of "patch motifs" for learning from past fixes.
    A patch motif is a representation of a bug fix that can be searched
    for similarity.
    """
    def __init__(self):
        kb_path_str = os.environ.get("KB_PATH")
        kb_path = Path(kb_path_str) if kb_path_str else None
        self.db_client = VectorDBClient(collection_name="patch_motifs", path=kb_path)

    def _create_document_from_patch(
        self,
        patch_content: str,
        source_file: str,
        error_log: str
    ) -> str:
        """Creates a single text document from the components of a bug fix."""
        # The document is a simple concatenation of the context.
        # More sophisticated representations could be used in the future.
        return f"File: {source_file}\nError: {error_log}\nPatch:\n{patch_content}"

    def add_motif(
        self,
        patch_content: str,
        source_file: str,
        error_log: str
    ):
        """
        Adds a new patch motif to the library.

        Args:
            patch_content: The diff content of the patch.
            source_file: The path to the file that was patched.
            error_log: The error log associated with the bug.
        """
        document = self._create_document_from_patch(patch_content, source_file, error_log)

        # Create a stable ID for the document
        doc_id = hashlib.sha256(document.encode()).hexdigest()

        metadata = {
            "source_file": source_file,
            "patch": patch_content
        }

        print(f"KB: Adding new patch motif for {source_file} to knowledge base.")
        self.db_client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata]
        )

    def find_similar_motifs(
        self,
        error_log: str,
        file_path: str,
        n_results: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Finds patch motifs that are similar to the current bug context.

        Args:
            error_log: The error log of the current bug.
            file_path: The path of the file suspected to contain the bug.
            n_results: The number of similar motifs to return.

        Returns:
            A list of similar motifs found in the database.
        """
        # The query is a combination of the file path and the error log
        query_text = f"File: {file_path}\nError: {error_log}"

        print(f"KB: Querying for motifs similar to bug in {file_path}.")
        return self.db_client.query(query_text, n_results=n_results)
