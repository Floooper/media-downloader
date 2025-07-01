import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database import get_db
from ..models.tables import Download
from ..models.schemas import Download as DownloadSchema
from ..models.enums import DownloadStatus
from ..services_manager import services
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/queue", tags=["queue"])

class QueueItem(BaseModel):
    """Queue item with position information"""
    download_id: int
    position: int

class QueueStats(BaseModel):
    """Queue statistics"""
    total_items: int
    active_downloads: int
    queued_downloads: int
    completed_downloads: int
    failed_downloads: int
    total_progress: float
    average_speed: float

@router.get("/", response_model=List[DownloadSchema])
async def get_queue(
    status: Optional[List[DownloadStatus]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get current download queue
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        return await queue_service.get_queue(status)

    except SQLAlchemyError as e:
        logger.error(f"Database error in get_queue: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue")

@router.post("/reorder", response_model=List[QueueItem])
async def reorder_queue(
    items: List[QueueItem],
    db: Session = Depends(get_db)
):
    """
    Reorder items in the download queue
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        # Validate all download IDs exist
        download_ids = [item.download_id for item in items]
        downloads = db.query(Download).filter(Download.id.in_(download_ids)).all()
        if len(downloads) != len(items):
            raise HTTPException(status_code=400, detail="One or more invalid download IDs")

        # Update queue order
        return await queue_service.reorder_queue(items)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to reorder queue")

@router.post("/clear", response_model=dict)
async def clear_queue(
    status: Optional[List[DownloadStatus]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Clear the download queue
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        cleared_count = await queue_service.clear_queue(status)
        return {
            "message": "Queue cleared successfully",
            "cleared_items": cleared_count
        }

    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear queue")

@router.get("/stats", response_model=QueueStats)
async def get_queue_stats(db: Session = Depends(get_db)):
    """
    Get queue statistics
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        return await queue_service.get_stats()

    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue statistics")

@router.post("/{download_id}/move", response_model=QueueItem)
async def move_in_queue(
    download_id: int = Path(..., ge=1),
    position: int = Query(..., ge=0),
    db: Session = Depends(get_db)
):
    """
    Move a download to a specific position in the queue
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        download = db.query(Download).get(download_id)
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")

        return await queue_service.move_download(download_id, position)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving download in queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to move download")

@router.post("/{download_id}/prioritize")
async def prioritize_download(
    download_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Move a download to the top of the queue
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        download = db.query(Download).get(download_id)
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")

        await queue_service.move_download(download_id, 0)
        return {"message": "Download prioritized successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prioritizing download: {e}")
        raise HTTPException(status_code=500, detail="Failed to prioritize download")

@router.post("/optimize")
async def optimize_queue(db: Session = Depends(get_db)):
    """
    Optimize queue order based on various factors
    """
    try:
        queue_service = services.get_queue_manager()
        if not queue_service:
            raise HTTPException(status_code=503, detail="Queue service unavailable")

        optimized_queue = await queue_service.optimize_queue()
        return {
            "message": "Queue optimized successfully",
            "queue": optimized_queue
        }

    except Exception as e:
        logger.error(f"Error optimizing queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize queue")
