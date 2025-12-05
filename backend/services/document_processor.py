"""
Asynchronous Document Processing Service
Handles document parsing, chunking, and embedding in background
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from sqlalchemy.orm import Session

from api.config import settings
from api.db import SessionLocal
from models.document_models import Document, DocumentStatus, DocumentType
from models.chunk_models import Chunk
from services.parser import DocumentParser
from services.chunker import get_chunker
from services.retriever import get_retriever
from services.llm import get_llm_client
from utils.hash import compute_text_hash


class DocumentProcessor:
    """Background document processing service"""

    @staticmethod
    def process_document(document_id: int) -> Dict[str, Any]:
        """
        Process a document asynchronously

        Steps:
        1. Parse document (PARSING)
        2. Chunk text (CHUNKING)
        3. Generate embeddings (EMBEDDING)
        4. Mark as READY or FAILED

        Args:
            document_id: Document ID to process

        Returns:
            Processing result dictionary
        """
        db: Session = SessionLocal()

        try:
            # Fetch document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                return {"success": False, "error": "Document not found"}

            logger.info(f"[Doc {document_id}] Starting background processing: {document.filename}")

            # ========== Step 1: Parse Document ==========
            document.status = DocumentStatus.PARSING
            db.commit()

            try:
                parsed_data = DocumentParser.parse(
                    str(document.storage_path),
                    document.file_type
                )

                document.parsed_text = parsed_data["text"]
                document.page_count = parsed_data.get("page_count")
                document.word_count = parsed_data.get("word_count")

                # Update metadata
                metadata = parsed_data.get("metadata", {})
                document.title = metadata.get("title") or document.filename
                document.author = metadata.get("author")
                document.subject = metadata.get("subject")

                document.parsed_at = datetime.utcnow()
                db.commit()

                logger.info(f"[Doc {document_id}] Parsing completed: {document.word_count} words, {document.page_count} pages")

                # Generate summary after parsing
                try:
                    llm = get_llm_client()
                    summary = llm.generate_summary(parsed_data["text"], document.filename)
                    document.summary = summary
                    db.commit()
                    logger.info(f"[Doc {document_id}] Summary generated successfully")
                except Exception as e:
                    logger.warning(f"[Doc {document_id}] Summary generation failed: {e}")
                    # Don't fail the entire process if summary fails
                    document.summary = "摘要生成失败"

            except Exception as e:
                logger.error(f"[Doc {document_id}] Parsing failed: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = f"Parsing failed: {str(e)}"
                db.commit()
                return {"success": False, "error": str(e), "stage": "parsing"}

            # ========== Step 2: Chunk Text ==========
            # Add CHUNKING status (need to add to enum first)
            document.status = DocumentStatus.EMBEDDING  # Using EMBEDDING for now, will add CHUNKING later
            db.commit()

            try:
                chunker = get_chunker()
                text_chunks = chunker.chunk_text(parsed_data["text"])

                logger.info(f"[Doc {document_id}] Chunking completed: {len(text_chunks)} chunks")

            except Exception as e:
                logger.error(f"[Doc {document_id}] Chunking failed: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = f"Chunking failed: {str(e)}"
                db.commit()
                return {"success": False, "error": str(e), "stage": "chunking"}

            # ========== Step 3: Save Chunks to Database ==========
            try:
                # First, delete any existing chunks and vectors for this document (in case of reprocessing)
                existing_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).all()
                if existing_chunks:
                    logger.info(f"[Doc {document_id}] Deleting {len(existing_chunks)} existing chunks and vectors")

                    # Delete vectors from Qdrant
                    try:
                        retriever = get_retriever()
                        retriever.delete_document(document.id)
                        logger.info(f"[Doc {document_id}] Deleted vectors from Qdrant")
                    except Exception as e:
                        logger.warning(f"[Doc {document_id}] Failed to delete Qdrant vectors: {e}")

                    # Delete chunks from database
                    for old_chunk in existing_chunks:
                        db.delete(old_chunk)
                    db.commit()

                chunk_records = []
                chunk_objects = []

                for idx, text in enumerate(text_chunks):
                    chunk = Chunk(
                        document_id=document.id,
                        text=text,
                        text_hash=compute_text_hash(text),
                        chunk_index=idx,
                        vector_id=f"doc_{document.id}_chunk_{idx}",
                    )
                    db.add(chunk)
                    chunk_objects.append(chunk)

                # Flush to assign chunk IDs
                db.flush()

                for chunk in chunk_objects:
                    chunk_records.append({
                        "chunk_id": chunk.id,
                        "document_id": document.id,
                        "text": chunk.text,
                        "vector_id": chunk.vector_id,
                    })

                db.commit()

                logger.info(f"[Doc {document_id}] Chunks saved to database")

            except Exception as e:
                logger.error(f"[Doc {document_id}] Chunk saving failed: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = f"Chunk saving failed: {str(e)}"
                db.commit()
                return {"success": False, "error": str(e), "stage": "chunk_saving"}

            # ========== Step 4: Generate Embeddings ==========
            try:
                retriever = get_retriever()
                retriever.add_chunks(chunk_records)

                logger.info(f"[Doc {document_id}] Embeddings generated and stored")

            except Exception as e:
                logger.error(f"[Doc {document_id}] Embedding generation failed: {e}")
                document.status = DocumentStatus.FAILED
                document.error_message = f"Embedding failed: {str(e)}"
                db.commit()
                return {"success": False, "error": str(e), "stage": "embedding"}

            # ========== Step 5: Mark as READY ==========
            document.status = DocumentStatus.READY
            db.commit()

            logger.info(f"[Doc {document_id}] Processing completed successfully: {len(text_chunks)} chunks")

            return {
                "success": True,
                "document_id": document.id,
                "chunks": len(text_chunks),
                "pages": document.page_count,
                "words": document.word_count,
            }

        except Exception as e:
            logger.error(f"[Doc {document_id}] Unexpected error: {e}")
            if 'document' in locals() and document:
                document.status = DocumentStatus.FAILED
                document.error_message = f"Processing failed: {str(e)}"
                db.commit()
            return {"success": False, "error": str(e), "stage": "unknown"}

        finally:
            db.close()


# Singleton instance
_processor: DocumentProcessor | None = None


def get_document_processor() -> DocumentProcessor:
    """Get or create the document processor singleton"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor
