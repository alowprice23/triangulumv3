import unittest
from unittest.mock import patch, MagicMock

# Since chromadb can be slow to import and initialize, we will heavily mock it.
# A real test suite might have separate, slower integration tests for this.

from kb.vector_db import VectorDBClient
from kb.patch_motif_library import PatchMotifLibrary

class TestKnowledgeBase(unittest.TestCase):

    @patch('chromadb.Client')
    def test_vector_db_initialization(self, mock_chroma_client):
        """Test that the VectorDBClient initializes correctly."""
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection

        db = VectorDBClient()

        self.assertIsNotNone(db)
        mock_chroma_client.return_value.get_or_create_collection.assert_called_with(name="patch_motifs")

    @patch('chromadb.Client')
    def test_vector_db_add_and_query(self, mock_chroma_client):
        """Test the add and query methods, mocking the chromadb collection."""
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection

        db = VectorDBClient()

        # Test add
        db.add_documents(
            ids=["1"],
            documents=["doc1"],
            metadatas=[{"file": "f1"}]
        )
        mock_collection.add.assert_called_once_with(
            documents=["doc1"],
            metadatas=[{"file": "f1"}],
            ids=["1"]
        )

        # Test query
        mock_collection.query.return_value = {
            "ids": [["1"]],
            "documents": [["doc1"]],
            "metadatas": [[{"file": "f1"}]],
            "distances": [[0.1]]
        }
        results = db.query("test query")
        mock_collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=3
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")

    @patch('kb.patch_motif_library.VectorDBClient')
    def test_patch_motif_library_add(self, mock_vector_db_client_class):
        """Test adding a motif to the library."""
        mock_db_instance = MagicMock()
        mock_vector_db_client_class.return_value = mock_db_instance

        library = PatchMotifLibrary()
        library.add_motif(
            patch_content="diff...",
            source_file="file.py",
            error_log="error..."
        )

        self.assertTrue(mock_db_instance.add_documents.called)
        # Check that the document content is what we expect
        args, kwargs = mock_db_instance.add_documents.call_args
        self.assertIn("File: file.py", kwargs["documents"][0])
        self.assertIn("Error: error...", kwargs["documents"][0])
        self.assertIn("Patch:\ndiff...", kwargs["documents"][0])

    @patch('kb.patch_motif_library.VectorDBClient')
    def test_patch_motif_library_find(self, mock_vector_db_client_class):
        """Test finding a motif in the library."""
        mock_db_instance = MagicMock()
        mock_vector_db_client_class.return_value = mock_db_instance

        library = PatchMotifLibrary()
        library.find_similar_motifs(
            error_log="error...",
            file_path="file.py"
        )

        mock_db_instance.query.assert_called_once()
        args, kwargs = mock_db_instance.query.call_args
        self.assertIn("File: file.py", args[0])
        self.assertIn("Error: error...", args[0])


if __name__ == '__main__':
    unittest.main()
