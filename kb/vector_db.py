import chromadb
from typing import List, Dict, Any

from pathlib import Path
from typing import Optional

class VectorDBClient:
    """
    A vector database client using ChromaDB, supporting both in-memory and
    persistent storage.
    """
    def __init__(self, collection_name: str = "patch_motifs", path: Optional[Path] = None):
        """
        Initializes the ChromaDB client.

        Args:
            collection_name: The name of the collection to use.
            path: If provided, a persistent client will be created at this path.
                  If None, an ephemeral in-memory client will be used.
        """
        if path:
            # Persistent client
            self.client = chromadb.PersistentClient(path=str(path))
        else:
            # Ephemeral in-memory client
            self.client = chromadb.Client()

        try:
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            # Handle potential initialization errors
            raise RuntimeError(f"Failed to initialize ChromaDB collection: {e}") from e

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        Adds documents and their embeddings to the collection.

        Args:
            ids: A list of unique IDs for the documents.
            documents: A list of the text documents to be embedded.
            metadatas: A list of dictionaries containing metadata for each document.
        """
        if not (len(ids) == len(documents) == len(metadatas)):
            raise ValueError("Length of ids, documents, and metadatas must be the same.")

        if not ids:
            return # Nothing to add

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            # ChromaDB can have various runtime errors
            print(f"Error adding documents to ChromaDB: {e}")


    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the collection to find the most similar documents.

        Args:
            query_text: The text to find similar documents for.
            n_results: The number of results to return.

        Returns:
            A list of dictionaries, where each dictionary represents a similar document.
            Returns an empty list if an error occurs.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            # The query result is a dictionary containing lists for ids, documents, etc.
            # We want to re-format this into a list of result objects.
            formatted_results = []
            if not results or not results.get("ids"):
                return []

            result_ids = results["ids"][0]
            result_docs = results["documents"][0]
            result_metadatas = results["metadatas"][0]
            result_distances = results["distances"][0]

            for i in range(len(result_ids)):
                formatted_results.append({
                    "id": result_ids[i],
                    "document": result_docs[i],
                    "metadata": result_metadatas[i],
                    "distance": result_distances[i]
                })

            return formatted_results
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []
