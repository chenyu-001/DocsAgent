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
    """Reprocess all documents stuck in UPLOADING status"""
    db: Session = SessionLocal()
    processor = DocumentProcessor()

    try:
        # Find all UPLOADING documents
        documents = db.query(Document).filter(
            Document.status == DocumentStatus.UPLOADING
        ).all()

        if not documents:
            logger.info("No documents in UPLOADING status found")
            return

        logger.info(f"Found {len(documents)} documents in UPLOADING status")

        # Process each document
        for doc in documents:
            logger.info(f"Processing document {doc.id}: {doc.filename}")
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
