from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

from discovery.code_graph import CodeGraph, CodeGraphSymbol

# It's good practice to reuse the model instance if possible.
# For now, we load it here. A more advanced implementation might share one instance
# across the application.
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2', cache_folder="./embedding_cache")

def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculates cosine similarity between two vectors."""
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_symbols(
    code_graph: CodeGraph,
    query_text: str,
    top_k: int = 5
) -> List[Tuple[CodeGraphSymbol, float]]:
    """
    Finds the most semantically similar code symbols in the graph to a given query text.

    Args:
        code_graph: The CodeGraph containing all the symbol information and embeddings.
        query_text: The text to search for (e.g., an error message).
        top_k: The number of similar symbols to return.

    Returns:
        A list of tuples, where each tuple contains a CodeGraphSymbol and its
        similarity score to the query, sorted from most to least similar.
    """
    if not query_text:
        return []

    query_embedding = EMBEDDING_MODEL.encode(query_text)

    similarities = []
    for filepath, symbols in code_graph.symbol_index.items():
        for symbol in symbols:
            if symbol.embedding is not None:
                sim = _cosine_similarity(query_embedding, np.array(symbol.embedding))
                similarities.append((symbol, sim, filepath))

    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Return the top_k symbols and their scores
    # We need to add the filepath back to the symbol object for context
    results = []
    for symbol, score, filepath in similarities[:top_k]:
        # A bit of a hack to add filepath context for the Analyst
        symbol_with_context = symbol.copy()
        symbol_with_context.name = f"{filepath}::{symbol.name}"
        results.append((symbol_with_context, score))

    return results
