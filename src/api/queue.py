from fastapi import APIRouter, HTTPException
from typing import List, Dict
from ..services_manager import services
from ..models.download import Download

router = APIRouter(prefix="/api/queue", tags=["queue"])

# Use singleton services
download_service = services.get_download_service()
queue_manager = services.get_queue_manager()

@router.get("/status")
async def get_queue_status() -> Dict:
    """Get current queue status."""
    return await queue_manager.get_queue_status()

@router.get("/")
async def get_queue() -> List[Download]:
    """Get all downloads in the queue."""
    return await queue_manager.get_queue()

@router.post("/{download_id}/move-up")
async def move_download_up(download_id: int):
    """Move a download up in the queue."""
    try:
        result = await queue_manager.move_up(download_id)
        if result:
            return {"message": f"Download {download_id} moved up in queue"}
        else:
            raise HTTPException(status_code=400, detail="Failed to move download up")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{download_id}/move-down")
async def move_download_down(download_id: int):
    """Move a download down in the queue."""
    try:
        result = await queue_manager.move_down(download_id)
        if result:
            return {"message": f"Download {download_id} moved down in queue"}
        else:
            raise HTTPException(status_code=400, detail="Failed to move download down")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{download_id}")
async def remove_from_queue(download_id: int):
    """Remove a download from the queue."""
    try:
        result = await queue_manager.remove_from_queue(download_id)
        if not result:
            raise HTTPException(status_code=404, detail="Download not found in queue")
        return {"message": f"Download {download_id} removed from queue"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clear")
async def clear_queue():
    """Clear all downloads from the queue."""
    try:
        cleared_count = await queue_manager.clear_queue()
        return {"message": f"Cleared {cleared_count} downloads from queue"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{download_id}/pause")
async def pause_download(download_id: int):
    """Pause a download."""
    try:
        result = await download_service.pause_download(download_id)
        if not result:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} paused"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{download_id}/resume")
async def resume_download(download_id: int):
    """Resume a download."""
    try:
        result = await download_service.resume_download(download_id)
        if not result:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} resumed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{download_id}/position/{new_position}")
async def set_download_position(download_id: int, new_position: int):
    """Set a download to a specific position in the queue."""
    try:
        result = await queue_manager.set_position(download_id, new_position)
        if not result:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} moved to position {new_position}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
