import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx
from pydantic import BaseModel, Field

from discovery.repo_scanner import RepoScanner
from discovery.ignore_rules import IgnoreRules
from adapters.base_adapter import LanguageAdapter
from sentence_transformers import SentenceTransformer

# --- Data Models for the Code Graph ---

class CodeGraphFile(BaseModel):
    """Represents a single file in the repository manifest."""
    path: str
    hash: str
    loc: int

class CodeGraphSymbol(BaseModel):
    """Represents a single symbol (function, class, etc.) in the index."""
    name: str
    type: str
    start_line: int
    end_line: int
    dependencies: List[str] = Field(default_factory=list)
    source_code: str
    embedding: Optional[List[float]] = None

class CodeGraph(BaseModel):
    """
    A comprehensive, serializable representation of a repository's structure,
    dependencies, and content. This is the "Advanced Encoding System".
    """
    metadata: Dict[str, Any] = Field(default_factory=dict)
    manifest: List[CodeGraphFile] = Field(default_factory=list)
    symbol_index: Dict[str, List[CodeGraphSymbol]] = Field(default_factory=dict)
    dependency_graph: nx.DiGraph = Field(default_factory=nx.DiGraph)
    language: str

    class Config:
        arbitrary_types_allowed = True # To allow networkx.DiGraph

# --- Builder Class ---

class CodeGraphBuilder:
    """
    Orchestrates the various discovery tools to build a complete CodeGraph.
    """
    def __init__(self, repo_root: Path, adapter: LanguageAdapter, ignore_rules: Optional[IgnoreRules] = None):
        self.repo_root = repo_root
        self.adapter = adapter
        self.ignore_rules = ignore_rules or IgnoreRules(project_root=self.repo_root)
        self.scanner = RepoScanner(ignore_rules=self.ignore_rules)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder="./embedding_cache")

    def build(self) -> CodeGraph:
        """
        Executes the full analysis process and returns a CodeGraph.
        """
        start_time = time.time()

        # 1. Scan repository to get the file manifest
        repo_manifest_raw = self.scanner.scan(self.repo_root)
        manifest = [CodeGraphFile(**item) for item in repo_manifest_raw]
        scope = [item.path for item in manifest]

        # 2. Use the adapter to build the symbol index
        symbol_index_raw = self.adapter.build_symbol_index(self.repo_root, scope)

        # 3. Enhance symbol index with embeddings
        symbol_index = {}
        for filepath, symbols in symbol_index_raw.items():
            symbol_models = []
            for sym in symbols:
                source_code = sym.get("source_code", "")
                embedding = self.embedding_model.encode(source_code).tolist() if source_code else None
                symbol_models.append(CodeGraphSymbol(**sym, embedding=embedding))
            symbol_index[filepath] = symbol_models

        # 4. Use the adapter to build the dependency graph
        dependency_graph = self.adapter.build_dependency_graph(symbol_index_raw, scope)

        end_time = time.time()

        return CodeGraph(
            metadata={
                "repo_root": str(self.repo_root),
                "timestamp": end_time,
                "build_duration_seconds": end_time - start_time,
                "total_files": len(manifest),
                "total_symbols": sum(len(s) for s in symbol_index.values()),
            },
            manifest=manifest,
            symbol_index=symbol_index,
            dependency_graph=dependency_graph,
            language=type(self.adapter).__name__.replace("Adapter", "").lower()
        )
