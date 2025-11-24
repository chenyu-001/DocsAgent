"""Document Upload Route"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
import shutil

from api.db import get_db
from api.auth import get_current_active_user
from api.config import settings
from models.user_models import User
from models.document_models import Document, DocumentType, DocumentStatus
from models.folder_models import Folder
from utils.hash import compute_file_hash
from services.parser import DocumentParser
from services.chunker import get_chunker
from services.retriever import get_retriever
from models.chunk_models import Chunk
from loguru import logger

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload and process document

    Process flow:
    1. Validate folder (if provided)
    2. Save file
    3. Compute hash and check duplicates
    4. Parse document
    5. Text chunking
    6. Generate embeddings and store in vector database

    Parameters:
    - **file**: File to upload (required)
    - **folder_id**: Folder ID to organize document (optional)
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
        # 1. Save file
        upload_dir = Path(settings.upload_path)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Compute file hash
        file_hash = compute_file_hash(file_path)

        # Check if file already exists
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing_doc:
            file_path.unlink()  # Delete duplicate file
            return {"message": "File already exists", "document_id": existing_doc.id}

        # 3. Determine file type
        suffix = file.filename.split(".")[-1].lower()
        file_type_map = {
            "pdf": DocumentType.PDF,
            "docx": DocumentType.DOCX,
            "pptx": DocumentType.PPTX,
            "txt": DocumentType.TXT,
            "md": DocumentType.MD,
        }
        file_type = file_type_map.get(suffix, DocumentType.OTHER)

        # 4. Create document record
        document = Document(
            filename=file.filename,
            file_hash=file_hash,
            file_type=file_type,
            file_size=file_path.stat().st_size,
            storage_path=str(file_path),
            status=DocumentStatus.PARSING,
            owner_id=current_user.id,
            folder_id=folder_id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Starting to parse document: {file.filename} (ID: {document.id})")

        # 5. Parse document
        try:
            parsed_data = DocumentParser.parse(str(file_path), file_type)

            document.parsed_text = parsed_data["text"]
            document.page_count = parsed_data.get("page_count")
            document.word_count = parsed_data.get("word_count")

            # Update metadata
            metadata = parsed_data.get("metadata", {})
            document.title = metadata.get("title") or file.filename
            document.author = metadata.get("author")
            document.subject = metadata.get("subject")

            document.status = DocumentStatus.EMBEDDING
            db.commit()

        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Document parsing failed: {e}")

        # 6. Text chunking
        chunker = get_chunker()
        text_chunks = chunker.chunk_text(parsed_data["text"])

        # 7. Save chunks to database and prepare for embedding
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

        # Flush to assign chunk IDs before preparing Qdrant payloads
        db.flush()

        for chunk in chunk_objects:
            chunk_records.append({
                "chunk_id": chunk.id,
                "document_id": document.id,
                "text": chunk.text,
                "vector_id": chunk.vector_id,
            })

        db.commit()

        # 8. Generate embeddings and store to Qdrant
        try:
            retriever = get_retriever()
            retriever.add_chunks(chunk_records)

            document.status = DocumentStatus.READY
            db.commit()

            logger.info(f"Document processing completed: {file.filename} ({len(text_chunks)} chunks)")

            return {
                "message": "Upload successful",
                "document_id": document.id,
                "filename": document.filename,
                "chunks": len(text_chunks),
            }

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            document.status = DocumentStatus.FAILED
            document.error_message = f"Embedding failed: {str(e)}"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        if 'document' in locals() and document.status == DocumentStatus.EMBEDDING:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))


from utils.hash import compute_text_hash  # Import at the end to avoid circular import
