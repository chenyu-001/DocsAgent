"""Retrieval-augmented question answering service."""
from __future__ import annotations

import time
from typing import Dict, List

from loguru import logger

from api.config import settings
from services.retriever import get_retriever
from services.llm import get_llm_client


class QAService:
    """Combine retriever and LLM to answer user questions."""

    def __init__(self):
        self.retriever = get_retriever()
        self.llm = get_llm_client()

    def _build_context(self, hits: List[Dict]) -> str:
        """Create a numbered context block for the LLM prompt."""
        parts = []
        for idx, hit in enumerate(hits, start=1):
            parts.append(f"[{idx}] 文档ID: {hit['document_id']}\n{hit['text']}")
        return "\n\n".join(parts)

    def answer_question(self, question: str, top_k: int | None = None) -> Dict:
        """Retrieve relevant chunks and generate an answer."""
        retrieval_start = time.perf_counter()
        hits = self.retriever.search(question, top_k=top_k or settings.FINAL_TOP_K)
        retrieval_time = time.perf_counter() - retrieval_start

        if not hits:
            return {
                "question": question,
                "answer": "未在文档中找到相关信息，无法回答该问题。",
                "sources": [],
                "retrieval_time": retrieval_time,
                "llm_time": 0.0,
                "total_time": retrieval_time,
            }

        context = self._build_context(hits)

        llm_start = time.perf_counter()
        try:
            answer = self.llm.generate_answer(question, context)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"LLM generation failed: {exc}")
            answer = "生成回答时出现问题，请稍后重试。"
        llm_time = time.perf_counter() - llm_start

        return {
            "question": question,
            "answer": answer,
            "sources": hits,
            "retrieval_time": retrieval_time,
            "llm_time": llm_time,
            "total_time": retrieval_time + llm_time,
        }


_qa_service: QAService | None = None


def get_qa_service() -> QAService:
    """Get or create the QA service singleton."""
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service
