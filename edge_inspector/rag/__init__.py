"""Local offline RAG documentation assistant package."""

from edge_inspector.rag.assistant import (
    InspectionDocumentationAssistant,
    RagResponse,
)
from edge_inspector.rag.indexer import DocumentChunk, LocalDocumentIndexer
from edge_inspector.rag.retriever import BM25Retriever

__all__ = [
    "BM25Retriever",
    "DocumentChunk",
    "InspectionDocumentationAssistant",
    "LocalDocumentIndexer",
    "RagResponse",
]
