"""Industrial documentation assistant with 100% local, offline semantic citation retrieval."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from edge_inspector.rag.retriever import BM25Retriever

logger = logging.getLogger(__name__)


@dataclass
class RagResponse:
    query: str
    answer: str
    passages: List[Dict[str, Any]]
    citations: List[str]
    llm_used: bool
    retrieval_latency_ms: float
    mode: str  # "100%_LOCAL_OFFLINE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InspectionDocumentationAssistant:
    """Industrial knowledge assistant for shop floor operators. 100% local, zero external API calls."""

    def __init__(
        self,
        retriever: Optional[BM25Retriever] = None,
        max_concurrency: int = 1,
    ) -> None:
        self.retriever = retriever or BM25Retriever()
        # Resource gate: Semaphore limits concurrent RAG compute so vision pipeline is never starved
        self._gate = threading.Semaphore(max_concurrency)

    def query(self, question: str, top_k: int = 3) -> RagResponse:
        """Processes an operator inquiry using purely local factory specifications."""
        t0 = time.perf_counter_ns()

        # Acquire resource gate without blocking camera acquisitions indefinitely
        acquired = self._gate.acquire(blocking=True, timeout=2.0)
        if not acquired:
            return RagResponse(
                query=question,
                answer="System busy: Vision inspection pipeline has processing priority. Please retry query shortly.",
                passages=[],
                citations=[],
                llm_used=False,
                retrieval_latency_ms=0.0,
                mode="BUSY_GATED",
            )

        try:
            # Yield CPU time slice to real-time inspection thread
            time.sleep(0.002)

            passages = self.retriever.retrieve(question, top_k=top_k)
            t1 = time.perf_counter_ns()
            latency_ms = (t1 - t0) / 1_000_000.0

            citations = [f"{p['source_file']} § {p['section_heading']}" for p in passages]
            answer_text = self._build_offline_extractive_answer(question, passages, citations)

            return RagResponse(
                query=question,
                answer=answer_text,
                passages=passages,
                citations=citations,
                llm_used=False,
                retrieval_latency_ms=round(latency_ms, 2),
                mode="100%_LOCAL_OFFLINE",
            )

        finally:
            self._gate.release()

    def _build_offline_extractive_answer(
        self,
        question: str,
        passages: List[Dict[str, Any]],
        citations: List[str],
    ) -> str:
        """Produces clear, structured extractive passages from local documentation."""
        if not passages:
            return (
                "Local Documentation Search: No matching specifications found for your query. "
                "Consult the local can defect manual or check spelling."
            )

        lines = [
            f"### Verified Factory Specifications for: '{question}'",
            "*(100% local edge retrieval - zero API calls, air-gapped operation)*\n",
        ]

        for idx, p in enumerate(passages, start=1):
            lines.append(f"#### Citation [{idx}]: {p['doc_title']} - {p['section_heading']} (`{p['source_file']}`)")
            lines.append(f"> {p['content']}\n")

        lines.append(f"**Referenced Sources**: {', '.join(citations)}")
        return "\n".join(lines)
