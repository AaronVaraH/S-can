"""Lightweight BM25 semantic retriever for Raspberry Pi edge deployment."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from edge_inspector.rag.indexer import LocalDocumentIndexer, tokenize


class BM25Retriever:
    """Okapi BM25 semantic search engine running 100% offline with near-zero RAM overhead."""

    def __init__(
        self,
        index_path: str = "data/rag_index.json",
        documents_dir: str = "edge_inspector/rag/documents",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.index_path = Path(index_path)
        self.documents_dir = Path(documents_dir)
        self.k1 = k1
        self.b = b
        self.chunks: List[Dict[str, Any]] = []
        self.doc_frequencies: Dict[str, int] = {}
        self.avg_doc_length: float = 1.0
        self.total_docs: int = 0
        self.is_loaded = False
        self._load_or_build_index()

    def _load_or_build_index(self) -> None:
        """Loads existing index from disk or compiles index on first launch."""
        if not self.index_path.exists():
            indexer = LocalDocumentIndexer(str(self.documents_dir), str(self.index_path))
            indexer.build_index()

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = data.get("chunks", [])
            self.doc_frequencies = data.get("doc_frequencies", {})
            self.avg_doc_length = float(data.get("avg_doc_length", 1.0))
            self.total_docs = len(self.chunks)
            self.is_loaded = True
        except Exception:
            self.is_loaded = False

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Scores all indexed document chunks against query terms."""
        if not self.is_loaded or self.total_docs == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in self.chunks:
            chunk_tf = chunk.get("term_frequencies", {})
            chunk_len = chunk.get("token_count", 1)
            score = 0.0

            for q_term in query_tokens:
                if q_term in chunk_tf:
                    tf = chunk_tf[q_term]
                    n_q = self.doc_frequencies.get(q_term, 1)
                    # Robertson-Spärck Jones IDF with smoothing
                    idf = math.log(1.0 + (self.total_docs - n_q + 0.5) / (n_q + 0.5))

                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (chunk_len / self.avg_doc_length))
                    score += idf * (numerator / denominator)

            if score > 0.1:
                # Add title matching boost
                title_lower = chunk.get("doc_title", "").lower()
                heading_lower = chunk.get("section_heading", "").lower()
                for q_term in query_tokens:
                    if q_term in title_lower or q_term in heading_lower:
                        score *= 1.3

                scored_chunks.append((round(score, 3), chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = []
        for s, ch in scored_chunks[:top_k]:
            top_results.append({
                "score": s,
                "doc_title": ch.get("doc_title"),
                "section_heading": ch.get("section_heading"),
                "source_file": ch.get("source_file"),
                "content": ch.get("content"),
                "chunk_id": ch.get("chunk_id"),
            })

        return top_results
