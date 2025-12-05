"""Retrieval-augmented question answering service."""
from __future__ import annotations

import time
from typing import Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from api.config import settings
from api.db import SessionLocal
from models.document_models import Document
from services.retriever import get_retriever
from services.llm import get_llm_client


class QAService:
    """Combine retriever and LLM to answer user questions."""

    def __init__(self):
        self.retriever = get_retriever()
        self.llm = get_llm_client()

    def _enrich_hits_with_document_info(self, hits: List[Dict]) -> List[Dict]:
        """Enrich search hits with document metadata (filename, path, etc)"""
        if not hits:
            return hits

        db: Session = SessionLocal()
        try:
            # Get unique document IDs
            doc_ids = list(set(hit['document_id'] for hit in hits))

            # Query document info
            documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_info_map = {
                doc.id: {
                    "filename": doc.filename,
                    "folder_path": doc.folder.path if doc.folder else "/",
                    "title": doc.title or doc.filename,
                }
                for doc in documents
            }

            # Enrich hits with document info
            enriched_hits = []
            for hit in hits:
                doc_id = hit['document_id']
                doc_info = doc_info_map.get(doc_id, {})
                enriched_hits.append({
                    **hit,
                    "filename": doc_info.get("filename", "未知文档"),
                    "folder_path": doc_info.get("folder_path", "/"),
                    "title": doc_info.get("title", "未知标题"),
                })

            return enriched_hits

        finally:
            db.close()

    def _build_context(self, hits: List[Dict]) -> str:
        """Create a numbered context block for the LLM prompt with document info."""
        parts = []
        for idx, hit in enumerate(hits, start=1):
            doc_ref = f"📄 {hit.get('filename', '未知文档')} ({hit.get('folder_path', '/')})"
            parts.append(f"[文档{idx}] {doc_ref}\n{hit['text']}")
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

        # Enrich hits with document metadata
        enriched_hits = self._enrich_hits_with_document_info(hits)
        context = self._build_context(enriched_hits)

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
            "sources": enriched_hits,
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
