"""Lightweight, memory-efficient offline document indexer for Raspberry Pi."""

from __future__ import annotations

import glob
import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_title: str
    section_heading: str
    source_file: str
    content: str
    token_count: int
    term_frequencies: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "did", "do",
    "does", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "if", "in", "into", "is",
    "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of",
    "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same",
    "she", "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with",
}


def tokenize(text: str) -> List[str]:
    """Extracts normalized lowercase word tokens, ignoring punctuation and stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


class LocalDocumentIndexer:
    """Builds and stores a compact BM25 index of local factory inspection documentation."""

    def __init__(self, documents_dir: str = "edge_inspector/rag/documents", index_path: str = "data/rag_index.json") -> None:
        self.documents_dir = Path(documents_dir)
        self.index_path = Path(index_path)
        self.chunks: List[DocumentChunk] = []
        self.doc_frequencies: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0

    def parse_markdown_document(self, file_path: Path) -> List[DocumentChunk]:
        """Splits markdown file into logical chunks by sections."""
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        doc_title = file_path.stem.replace("_", " ").title()
        chunks: List[DocumentChunk] = []
        current_heading = "Overview"
        current_lines: List[str] = []

        chunk_counter = 0

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("# "):
                doc_title = line_stripped.lstrip("#").strip()
            elif line_stripped.startswith("## ") or line_stripped.startswith("### "):
                if current_lines:
                    content_str = "\n".join(current_lines).strip()
                    if len(content_str) > 30:
                        tokens = tokenize(content_str)
                        tf = {}
                        for t in tokens:
                            tf[t] = tf.get(t, 0) + 1
                        chunk_counter += 1
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{file_path.stem}_{chunk_counter}",
                                doc_title=doc_title,
                                section_heading=current_heading,
                                source_file=file_path.name,
                                content=content_str,
                                token_count=len(tokens),
                                term_frequencies=tf,
                            )
                        )
                    current_lines = []
                current_heading = line_stripped.lstrip("#").strip()
            else:
                current_lines.append(line)

        # Flush trailing section
        if current_lines:
            content_str = "\n".join(current_lines).strip()
            if len(content_str) > 30:
                tokens = tokenize(content_str)
                tf = {}
                for t in tokens:
                    tf[t] = tf.get(t, 0) + 1
                chunk_counter += 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{file_path.stem}_{chunk_counter}",
                        doc_title=doc_title,
                        section_heading=current_heading,
                        source_file=file_path.name,
                        content=content_str,
                        token_count=len(tokens),
                        term_frequencies=tf,
                    )
                )

        return chunks

    def build_index(self) -> Dict[str, Any]:
        """Indexes all markdown files in documents_dir while reserving CPU."""
        md_files = sorted(list(self.documents_dir.glob("*.md")) + list(self.documents_dir.glob("*.txt")))
        self.chunks = []
        self.doc_frequencies = {}

        for f in md_files:
            # Yield CPU slice so real-time vision processing is not delayed
            time.sleep(0.005)
            doc_chunks = self.parse_markdown_document(f)
            self.chunks.extend(doc_chunks)

        total_tokens = sum(c.token_count for c in self.chunks)
        self.avg_doc_length = float(total_tokens / len(self.chunks)) if self.chunks else 1.0

        # Calculate document frequencies
        for chunk in self.chunks:
            for term in chunk.term_frequencies.keys():
                self.doc_frequencies[term] = self.doc_frequencies.get(term, 0) + 1

        index_data = {
            "version": "1.0",
            "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_chunks": len(self.chunks),
            "avg_doc_length": self.avg_doc_length,
            "doc_frequencies": self.doc_frequencies,
            "chunks": [c.to_dict() for c in self.chunks],
        }

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

        return index_data
