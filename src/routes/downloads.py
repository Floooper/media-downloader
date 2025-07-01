import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database import get_db
from ..models.tables import Download, Tag
from ..models.schemas import (
    DownloadCreate, DownloadUpdate, Download as DownloadSchema,
    DownloadProgress, DownloadFilter, DownloadSort
)
from ..models.enums import DownloadStatus, DownloadType
from ..services_manager import services
from ..config import settings
from datetime import datetime
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/downloads", tags=["downloads"])

@router.get("/", response_model=List[DownloadSchema])
async def list_downloads(
    db: Session = Depends(get_db),
    filter: Optional[DownloadFilter] = None,
    sort: Optional[DownloadSort] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List downloads with filtering, sorting and pagination
    """
    try:
        query = db.query(Download)

        # Apply filters
        if filter:
            if filter.status:
                query = query.filter(Download.status.in_(filter.status))
            if filter.download_type:
                query = query.filter(Download.download_type.in_(filter.download_type))
            if filter.tag_ids:
                query = query.filter(Download.tags.any(Tag.id.in_(filter.tag_ids)))
            if filter.search:
                query = query.filter(Download.name.ilike(f"%{filter.search}%"))
            if filter.date_from:
                query = query.filter(Download.created_at >= filter.date_from)
            if filter.date_to:
                query = query.filter(Download.created_at <= filter.date_to)

        # Apply sorting
        if sort:
            if sort.direction == "desc":
                query = query.order_by(getattr(Download, sort.field).desc())
            else:
                query = query.order_by(getattr(Download, sort.field))
        else:
            query = query.order_by(Download.created_at.desc())

        # Apply pagination
        downloads = query.offset(offset).limit(limit).all()
        return downloads

    except SQLAlchemyError as e:
        logger.error(f"Database error in list_downloads: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in list_downloads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/nzb", response_model=DownloadSchema)
async def upload_nzb(
    file: UploadFile = File(...),
    path: Optional[str] = Query(None),
    tag_ids: List[int] = Query([]),
    db: Session = Depends(get_db)
):
    """
    Upload and process NZB file
    """
    try:
        # Validate file extension
        if not file.filename.lower().endswith('.nzb'):
            raise HTTPException(status_code=400, detail="Invalid file type. Must be .nzb")

        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        # Get download service
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        # Use specified path or default
        download_path = path or settings.DOWNLOAD_PATH
        os.makedirs(download_path, exist_ok=True)

        # Create download
        download = await download_service.add_nzb(
            nzb_content=content.decode(),
            download_path=download_path,
            filename=file.filename
        )

        # Add tags if specified
        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            if len(tags) != len(tag_ids):
                raise HTTPException(status_code=400, detail="One or more invalid tag IDs")
            download.tags.extend(tags)
            db.commit()

        return download

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing NZB upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to process NZB file")

@router.post("/magnet", response_model=DownloadSchema)
async def add_magnet(
    magnet_link: str = Query(..., min_length=20),
    path: Optional[str] = Query(None),
    tag_ids: List[int] = Query([]),
    db: Session = Depends(get_db)
):
    """
    Add magnet link download
    """
    try:
        if not settings.ENABLE_TORRENTS:
            raise HTTPException(status_code=403, detail="Torrent downloads are disabled")

        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        download_path = path or settings.DOWNLOAD_PATH
        os.makedirs(download_path, exist_ok=True)

        download = await download_service.add_magnet_download(
            magnet_link=magnet_link,
            download_path=download_path
        )

        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            if len(tags) != len(tag_ids):
                raise HTTPException(status_code=400, detail="One or more invalid tag IDs")
            download.tags.extend(tags)
            db.commit()

        return download

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing magnet link: {e}")
        raise HTTPException(status_code=500, detail="Failed to process magnet link")

@router.post("/{download_id}/pause", response_model=DownloadSchema)
async def pause_download(
    download_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Pause a download
    """
    try:
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        success = await download_service.pause_download(download_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")

        return await download_service.get_download(download_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing download {download_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause download")

@router.post("/{download_id}/resume", response_model=DownloadSchema)
async def resume_download(
    download_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Resume a paused download
    """
    try:
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        success = await download_service.resume_download(download_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")

        return await download_service.get_download(download_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming download {download_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume download")

@router.delete("/{download_id}")
async def delete_download(
    download_id: int = Path(..., ge=1),
    delete_files: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Delete a download and optionally its files
    """
    try:
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        success = await download_service.remove_download(download_id, delete_files)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")

        return {"message": "Download deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting download {download_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete download")

@router.patch("/{download_id}", response_model=DownloadSchema)
async def update_download(
    download_id: int = Path(..., ge=1),
    update: DownloadUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Update download information
    """
    try:
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        download = await download_service.get_download(download_id)
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")

        # Update tags if specified
        if update.tag_ids is not None:
            tags = db.query(Tag).filter(Tag.id.in_(update.tag_ids)).all()
            if len(tags) != len(update.tag_ids):
                raise HTTPException(status_code=400, detail="One or more invalid tag IDs")
            download.tags = tags

        # Update other fields
        for field, value in update.dict(exclude_unset=True).items():
            if field != 'tag_ids':
                setattr(download, field, value)

        updated_download = await download_service.update_download(download)
        return updated_download

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating download {download_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update download")

@router.get("/{download_id}/progress", response_model=DownloadProgress)
async def get_download_progress(
    download_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get current download progress
    """
    try:
        download_service = services.get_download_service()
        if not download_service:
            raise HTTPException(status_code=503, detail="Download service unavailable")

        progress = await download_service.get_progress(download_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Download not found")

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download progress {download_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download progress")
