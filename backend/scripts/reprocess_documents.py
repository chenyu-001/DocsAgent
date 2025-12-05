"""
Reprocess stuck documents in UPLOADING status
用于处理卡在 UPLOADING 状态的文档
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from api.db import SessionLocal
from models.document_models import Document, DocumentStatus
from services.document_processor import DocumentProcessor
from loguru import logger


def reprocess_all_uploading_documents():
    """Reprocess all documents that are not in READY status"""
    db: Session = SessionLocal()
    processor = DocumentProcessor()

    try:
        # Find all documents that are NOT in READY status
        # This includes: UPLOADING, PARSING, EMBEDDING, FAILED
        documents = db.query(Document).filter(
            Document.status != DocumentStatus.READY
        ).all()

        if not documents:
            logger.info("No documents need reprocessing (all are READY)")
            return

        logger.info(f"Found {len(documents)} documents to reprocess")
        logger.info(f"Status breakdown: {[(doc.id, doc.filename, doc.status.value) for doc in documents]}")

        # Process each document
        for doc in documents:
            logger.info(f"Processing document {doc.id}: {doc.filename} (current status: {doc.status.value})")
            try:
                result = processor.process_document(doc.id)
                if result["success"]:
                    logger.info(f"✅ Document {doc.id} processed successfully")
                else:
                    logger.error(f"❌ Document {doc.id} processing failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Document {doc.id} processing error: {e}")

        logger.info("All documents processed")

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting document reprocessing...")
    reprocess_all_uploading_documents()
    logger.info("Done!")
