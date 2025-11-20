"""
Document Management Routes
Provides APIs for listing, viewing, and managing uploaded documents
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from loguru import logger

from api.db import get_db
from api.auth import get_current_active_user
from models.user_models import User
from models.document_models import Document, DocumentStatus, DocumentType

router = APIRouter()


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    file_type: Optional[DocumentType] = Query(None, description="Filter by file type"),
    sort_by: str = Query("created_at", description="Sort field (created_at, filename, file_size)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    search: Optional[str] = Query(None, description="Search in filename"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List user's documents with pagination and filtering
    """
    try:
        # Build query
        query = db.query(Document).filter(Document.owner_id == current_user.id)

        # Apply filters
        if status:
            query = query.filter(Document.status == status)
        if file_type:
            query = query.filter(Document.file_type == file_type)
        if search:
            query = query.filter(Document.filename.ilike(f"%{search}%"))

        # Apply sorting
        sort_field = getattr(Document, sort_by, Document.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        documents = query.offset(offset).limit(page_size).all()

        # Convert to dict
        docs_list = [doc.to_dict() for doc in documents]

        return {
            "documents": docs_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get document details by ID
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document.to_dict(include_chunks=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a document (soft delete by marking status)
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database (CASCADE will delete chunks)
        db.delete(document)
        db.commit()

        logger.info(f"User {current_user.username} deleted document: {document.filename} (ID: {document_id})")

        return {"message": "Document deleted successfully", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/documents/stats/summary")
async def get_document_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get document statistics summary for current user
    """
    try:
        from sqlalchemy import func

        # Total documents
        total_docs = db.query(func.count(Document.id)).filter(
            Document.owner_id == current_user.id
        ).scalar()

        # Documents by status
        status_counts = db.query(
            Document.status,
            func.count(Document.id)
        ).filter(
            Document.owner_id == current_user.id
        ).group_by(Document.status).all()

        # Documents by type
        type_counts = db.query(
            Document.file_type,
            func.count(Document.id)
        ).filter(
            Document.owner_id == current_user.id
        ).group_by(Document.file_type).all()

        # Total storage used
        total_size = db.query(func.sum(Document.file_size)).filter(
            Document.owner_id == current_user.id
        ).scalar() or 0

        return {
            "total_documents": total_docs,
            "total_storage_bytes": total_size,
            "by_status": {status.value: count for status, count in status_counts},
            "by_type": {file_type.value: count for file_type, count in type_counts},
        }

    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
