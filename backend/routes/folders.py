"""Folder Management Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from api.db import get_db
from api.auth import get_current_active_user
from models.user_models import User
from models.folder_models import Folder
from loguru import logger

router = APIRouter()


# Pydantic models for request/response
class FolderCreate(BaseModel):
    """Folder creation request"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class FolderUpdate(BaseModel):
    """Folder update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class FolderResponse(BaseModel):
    """Folder response"""
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    path: str
    owner_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new folder

    - **name**: Folder name (required)
    - **description**: Folder description (optional)
    - **parent_id**: Parent folder ID (optional, NULL for root level)
    """
    try:
        # Calculate folder path
        if folder_data.parent_id:
            parent = db.query(Folder).filter(
                Folder.id == folder_data.parent_id,
                Folder.owner_id == current_user.id
            ).first()

            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")

            path = f"{parent.path}/{folder_data.name}"
        else:
            path = f"/{folder_data.name}"

        # Check if folder with same path already exists
        existing = db.query(Folder).filter(
            Folder.path == path,
            Folder.owner_id == current_user.id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Folder with this path already exists")

        # Create new folder
        folder = Folder(
            name=folder_data.name,
            description=folder_data.description,
            parent_id=folder_data.parent_id,
            path=path,
            owner_id=current_user.id,
        )

        db.add(folder)
        db.commit()
        db.refresh(folder)

        logger.info(f"Created folder: {folder.path} (ID: {folder.id})")

        return folder.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create folder: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[int] = Query(None, description="Parent folder ID (NULL for root level)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List folders

    - **parent_id**: Filter by parent folder ID (omit or set to null for root folders)
    """
    try:
        query = db.query(Folder).filter(Folder.owner_id == current_user.id)

        if parent_id is not None:
            query = query.filter(Folder.parent_id == parent_id)
        else:
            # Only return root folders when parent_id is not specified
            query = query.filter(Folder.parent_id == None)

        folders = query.order_by(Folder.name).all()

        return [folder.to_dict() for folder in folders]

    except Exception as e:
        logger.error(f"Failed to list folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/tree", response_model=List[dict])
async def get_folder_tree(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get folder tree structure

    Returns all folders in a hierarchical tree structure
    """
    try:
        # Get all folders
        folders = db.query(Folder).filter(
            Folder.owner_id == current_user.id
        ).order_by(Folder.path).all()

        # Build tree structure
        folder_map = {}
        root_folders = []

        for folder in folders:
            folder_dict = folder.to_dict()
            folder_dict['children'] = []
            folder_map[folder.id] = folder_dict

        for folder in folders:
            folder_dict = folder_map[folder.id]
            if folder.parent_id is None:
                root_folders.append(folder_dict)
            else:
                parent = folder_map.get(folder.parent_id)
                if parent:
                    parent['children'].append(folder_dict)

        return root_folders

    except Exception as e:
        logger.error(f"Failed to get folder tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get folder details"""
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return folder.to_dict()


@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update folder

    - **name**: New folder name
    - **description**: New description
    - **parent_id**: New parent folder ID (to move folder)
    """
    try:
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == current_user.id
        ).first()

        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Update fields
        if folder_data.name is not None:
            folder.name = folder_data.name

        if folder_data.description is not None:
            folder.description = folder_data.description

        if folder_data.parent_id is not None:
            # Verify parent exists and prevent circular reference
            if folder_data.parent_id == folder.id:
                raise HTTPException(status_code=400, detail="Cannot set folder as its own parent")

            parent = db.query(Folder).filter(
                Folder.id == folder_data.parent_id,
                Folder.owner_id == current_user.id
            ).first()

            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")

            # Check for circular reference
            current_parent = parent
            while current_parent:
                if current_parent.id == folder.id:
                    raise HTTPException(status_code=400, detail="Circular folder reference detected")
                current_parent = db.query(Folder).filter(
                    Folder.id == current_parent.parent_id
                ).first() if current_parent.parent_id else None

            folder.parent_id = folder_data.parent_id

        # Recalculate path
        if folder.parent_id:
            parent = db.query(Folder).filter(Folder.id == folder.parent_id).first()
            folder.path = f"{parent.path}/{folder.name}"
        else:
            folder.path = f"/{folder.name}"

        db.commit()
        db.refresh(folder)

        logger.info(f"Updated folder: {folder.path} (ID: {folder.id})")

        return folder.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update folder: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete folder

    Note: This will also delete all documents in the folder (CASCADE)
    """
    try:
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == current_user.id
        ).first()

        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Check if folder has children
        children = db.query(Folder).filter(Folder.parent_id == folder_id).count()
        if children > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete folder with subfolders. Delete subfolders first."
            )

        folder_name = folder.path
        db.delete(folder)
        db.commit()

        logger.info(f"Deleted folder: {folder_name} (ID: {folder_id})")

        return {"message": "Folder deleted successfully", "folder_id": folder_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete folder: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
