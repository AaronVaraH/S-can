"""Unit tests for offline local RAG documentation assistant."""

import pytest
from edge_inspector.rag.assistant import InspectionDocumentationAssistant
from edge_inspector.rag.retriever import BM25Retriever


def test_bm25_retriever():
    retriever = BM25Retriever()
    assert retriever.is_loaded is True
    assert retriever.total_docs > 0

    results = retriever.retrieve("double seam thickness tolerance overlap", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "score" in top
    assert "doc_title" in top
    assert "content" in top
    assert "source_file" in top


def test_rag_assistant_offline_mode():
    assistant = InspectionDocumentationAssistant()
    resp = assistant.query("What are the visual signs of rim dents and cut seams?")
    assert resp.mode == "100%_LOCAL_OFFLINE"
    assert resp.llm_used is False
    assert len(resp.passages) > 0
    assert len(resp.citations) > 0
    assert "### Verified Factory Specifications" in resp.answer
