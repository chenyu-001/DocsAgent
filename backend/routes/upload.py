"""Document Upload Route"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
import shutil
import uuid

from api.db import get_db
from api.auth import get_current_active_user
from api.config import settings
from models.user_models import User
from models.document_models import Document, DocumentType, DocumentStatus
from models.folder_models import Folder
from utils.hash import compute_file_hash
from services.document_processor import get_document_processor
from services.retriever import get_retriever
from loguru import logger

router = APIRouter()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    overwrite: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload document and process asynchronously

    NEW ASYNC FLOW:
    1. Validate folder (if provided)
    2. Save file to storage
    3. Compute hash and check duplicates
    4. Create document record (status: UPLOADING)
    5. Start background processing task
    6. Return immediately (user doesn't wait!)

    Background task will handle:
    - Parsing (PARSING)
    - Chunking (EMBEDDING)
    - Vector embedding (EMBEDDING)
    - Mark as READY or FAILED

    Parameters:
    - **file**: File to upload (required)
    - **folder_id**: Folder ID to organize document (optional)
    - **overwrite**: Overwrite existing file with same name (default: false)

    Returns:
    - Immediate response with document_id
    - Frontend can poll /documents/{id} to check processing status
    """
    try:
        # 1. Validate folder if provided
        if folder_id is not None:
            folder = db.query(Folder).filter(
                Folder.id == folder_id,
                Folder.owner_id == current_user.id
            ).first()

            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")

        # 2. Save file with UUID-based filename to avoid encoding issues
        upload_dir = Path(settings.upload_path)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename: UUID + original extension
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved: {file.filename} -> {unique_filename}")

        # 3. Compute file hash
        file_hash = compute_file_hash(file_path)

        # Check if file with same name and folder already exists (overwrite mode)
        existing_doc_by_name = db.query(Document).filter(
            Document.filename == file.filename,
            Document.folder_id == folder_id,
            Document.owner_id == current_user.id
        ).first()

        if existing_doc_by_name:
            # If overwrite flag is not set, ask for confirmation
            if not overwrite:
                return JSONResponse(
                    status_code=409,
                    content={
                        "detail": {
                            "code": "FILE_EXISTS",
                            "message": f"File '{file.filename}' already exists in this location. Do you want to overwrite it?",
                            "existing_document_id": existing_doc_by_name.id,
                            "filename": file.filename,
                            "folder_id": folder_id,
                            "temp_file_path": str(file_path)
                        }
                    }
                )

            # User confirmed overwrite - delete the old document
            logger.info(f"Overwriting existing document: {file.filename} (ID: {existing_doc_by_name.id})")

            # Delete the old file from storage if it exists
            old_file_path = Path(existing_doc_by_name.storage_path)
            if old_file_path.exists():
                old_file_path.unlink()

            # Delete vectors from Qdrant
            try:
                retriever = get_retriever()
                retriever.delete_document(existing_doc_by_name.id)
            except Exception as e:
                logger.warning(f"Failed to delete vectors for document {existing_doc_by_name.id}: {e}")

            # Delete the document record (will cascade delete chunks)
            db.delete(existing_doc_by_name)
            db.commit()

        # Check if file with same hash already exists (duplicate content)
        existing_doc_by_hash = db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.owner_id == current_user.id
        ).first()

        if existing_doc_by_hash:
            file_path.unlink()  # Delete duplicate file
            logger.info(f"Duplicate file detected: {file.filename} (existing ID: {existing_doc_by_hash.id})")
            return {
                "message": "File already exists",
                "document_id": existing_doc_by_hash.id,
                "status": existing_doc_by_hash.status.value
            }

        # 4. Determine file type
        suffix = file.filename.split(".")[-1].lower()
        file_type_map = {
            "pdf": DocumentType.PDF,
            "docx": DocumentType.DOCX,
            "pptx": DocumentType.PPTX,
            "txt": DocumentType.TXT,
            "md": DocumentType.MD,
        }
        file_type = file_type_map.get(suffix, DocumentType.OTHER)

        # 5. Create document record with UPLOADING status
        document = Document(
            filename=file.filename,
            file_hash=file_hash,
            file_type=file_type,
            file_size=file_path.stat().st_size,
            storage_path=str(file_path),
            status=DocumentStatus.UPLOADING,  # Start with UPLOADING
            owner_id=current_user.id,
            folder_id=folder_id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Document record created: {file.filename} (ID: {document.id}, Status: UPLOADING)")

        # 6. Start background processing
        processor = get_document_processor()
        background_tasks.add_task(processor.process_document, document.id)

        logger.info(f"Background processing started for document {document.id}")

        # 7. Return immediately - user doesn't wait!
        return {
            "message": "Upload successful - processing in background",
            "document_id": document.id,
            "filename": document.filename,
            "status": document.status.value,
            "file_size": document.file_size,
            "file_type": document.file_type.value,
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Clean up file if it was saved
        if 'file_path' in locals() and Path(file_path).exists():
            Path(file_path).unlink()
        raise HTTPException(status_code=500, detail=str(e))


from utils.hash import compute_text_hash  # Import at the end to avoid circular import
