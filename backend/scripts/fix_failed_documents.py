"""
Fix documents with missing or invalid file paths
用于修复文件路径不存在的失败文档
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from api.db import SessionLocal
from models.document_models import Document, DocumentStatus
from loguru import logger


def diagnose_failed_documents():
    """Diagnose and report on failed documents"""
    db: Session = SessionLocal()

    try:
        # Find all documents with issues
        all_documents = db.query(Document).all()

        issues = {
            "missing_files": [],
            "failed_status": [],
            "non_ready_status": [],
        }

        logger.info(f"Checking {len(all_documents)} documents...")

        for doc in all_documents:
            # Check if file exists
            file_path = Path(doc.storage_path)
            if not file_path.exists():
                issues["missing_files"].append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "storage_path": doc.storage_path,
                    "status": doc.status.value,
                    "error": doc.error_message,
                })

            # Check status
            if doc.status == DocumentStatus.FAILED:
                issues["failed_status"].append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "error": doc.error_message,
                    "file_exists": file_path.exists(),
                })

            if doc.status != DocumentStatus.READY:
                issues["non_ready_status"].append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                })

        # Report findings
        logger.info("\n" + "="*80)
        logger.info("DIAGNOSTIC REPORT")
        logger.info("="*80)

        logger.info(f"\n📁 Missing Files ({len(issues['missing_files'])} documents):")
        for issue in issues["missing_files"]:
            logger.warning(f"  - ID {issue['id']}: {issue['filename']}")
            logger.warning(f"    Path: {issue['storage_path']}")
            logger.warning(f"    Status: {issue['status']}")
            if issue['error']:
                logger.warning(f"    Error: {issue['error']}")

        logger.info(f"\n❌ Failed Status ({len(issues['failed_status'])} documents):")
        for issue in issues["failed_status"]:
            logger.warning(f"  - ID {issue['id']}: {issue['filename']}")
            logger.warning(f"    File exists: {issue['file_exists']}")
            logger.warning(f"    Error: {issue['error']}")

        logger.info(f"\n⏳ Non-Ready Status ({len(issues['non_ready_status'])} documents):")
        for issue in issues["non_ready_status"]:
            logger.info(f"  - ID {issue['id']}: {issue['filename']} ({issue['status']})")

        logger.info("\n" + "="*80)
        logger.info("RECOMMENDATIONS")
        logger.info("="*80)

        if issues["missing_files"]:
            logger.info("\n🔧 Missing files can be resolved by:")
            logger.info("  1. Re-uploading the documents (recommended)")
            logger.info("  2. Deleting the orphaned document records")
            logger.info("\nTo delete orphaned documents, run:")
            logger.info("  python scripts/fix_failed_documents.py --delete-orphaned")

        if issues["failed_status"]:
            logger.info("\n🔧 Failed documents can be resolved by:")
            logger.info("  1. Re-uploading if file is missing")
            logger.info("  2. Reprocessing if file exists")
            logger.info("\nTo reprocess failed documents with existing files, run:")
            logger.info("  python scripts/fix_failed_documents.py --reprocess-failed")

        if issues["non_ready_status"]:
            logger.info("\n🔧 Non-ready documents can be resolved by:")
            logger.info("  1. Waiting for background processing to complete")
            logger.info("  2. Reprocessing if stuck")
            logger.info("\nTo reprocess stuck documents, run:")
            logger.info("  python scripts/reprocess_documents.py")

    finally:
        db.close()


def delete_orphaned_documents():
    """Delete documents whose files don't exist"""
    db: Session = SessionLocal()

    try:
        all_documents = db.query(Document).all()
        deleted_count = 0

        for doc in all_documents:
            file_path = Path(doc.storage_path)
            if not file_path.exists():
                logger.info(f"Deleting orphaned document {doc.id}: {doc.filename}")
                db.delete(doc)
                deleted_count += 1

        if deleted_count > 0:
            db.commit()
            logger.info(f"✅ Deleted {deleted_count} orphaned documents")
        else:
            logger.info("✅ No orphaned documents found")

    except Exception as e:
        logger.error(f"Error deleting orphaned documents: {e}")
        db.rollback()
    finally:
        db.close()


def reprocess_failed_with_files():
    """Reprocess failed documents that have existing files"""
    from services.document_processor import DocumentProcessor

    db: Session = SessionLocal()
    processor = DocumentProcessor()

    try:
        # Find failed documents with existing files
        failed_docs = db.query(Document).filter(
            Document.status == DocumentStatus.FAILED
        ).all()

        candidates = []
        for doc in failed_docs:
            if Path(doc.storage_path).exists():
                candidates.append(doc)

        if not candidates:
            logger.info("No failed documents with existing files found")
            return

        logger.info(f"Found {len(candidates)} failed documents with existing files")

        for doc in candidates:
            logger.info(f"Reprocessing document {doc.id}: {doc.filename}")
            try:
                result = processor.process_document(doc.id)
                if result["success"]:
                    logger.info(f"✅ Successfully reprocessed document {doc.id}")
                else:
                    logger.error(f"❌ Failed to reprocess document {doc.id}: {result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Error reprocessing document {doc.id}: {e}")

        logger.info("Reprocessing complete")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose and fix failed documents")
    parser.add_argument(
        "--delete-orphaned",
        action="store_true",
        help="Delete documents whose files don't exist"
    )
    parser.add_argument(
        "--reprocess-failed",
        action="store_true",
        help="Reprocess failed documents that have existing files"
    )

    args = parser.parse_args()

    if args.delete_orphaned:
        logger.info("Deleting orphaned documents...")
        delete_orphaned_documents()
    elif args.reprocess_failed:
        logger.info("Reprocessing failed documents...")
        reprocess_failed_with_files()
    else:
        logger.info("Running diagnostic check...")
        diagnose_failed_documents()
