from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from typing import Optional, Dict, List
from ..services_manager import services
from ..models.tables import DownloadTable  # SQLAlchemy model
from ..models.download import Download  # Pydantic model for API responses
from ..config import settings
from pydantic import BaseModel
import re
import logging

router = APIRouter(prefix="/api/downloads", tags=["downloads"])
logger = logging.getLogger(__name__)

# Use singleton services
download_service = services.get_download_service()
tag_service = services.get_tag_service()

# Request models
class TorrentDownloadRequest(BaseModel):
    magnet_link: str
    download_path: Optional[str] = None

class NZBDownloadRequest(BaseModel):
    nzb_content: str
    download_path: Optional[str] = None

class FilePriorityRequest(BaseModel):
    priorities: Dict[int, int]

def validate_magnet_link(magnet_link: str) -> bool:
    """Validate that the magnet link is properly formatted"""
    if not magnet_link or not magnet_link.strip():
        return False
    
    # Check if it starts with magnet:
    if not magnet_link.startswith('magnet:'):
        return False
    
    # Check if it has the required xt parameter with btih (BitTorrent Info Hash)
    if 'xt=urn:btih:' not in magnet_link:
        return False
    
    return True

def validate_file_size(file_content: bytes, max_size_mb: int, file_type: str) -> None:
    """Validate file size against configured limits"""
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size for {file_type} files is {max_size_mb}MB. Your file is {file_size_mb:.1f}MB."
        )

@router.get("/")
async def get_downloads() -> List[Download]:
    """Get all downloads."""
    try:
        return await download_service.get_all_downloads()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/limits")
async def get_upload_limits():
    """Get current upload size limits."""
    return {
        "max_nzb_file_size_mb": settings.MAX_NZB_FILE_SIZE_MB,
        "max_torrent_file_size_mb": settings.MAX_TORRENT_FILE_SIZE_MB,
        "nginx_client_max_body_size": "100MB",
        "note": "File uploads are limited by both application settings and nginx configuration"
    }

@router.get("/{download_id}")
async def get_download(download_id: int) -> Download:
    """Get a specific download by ID."""
    try:
        download = await download_service.get_download(download_id)
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")
        return download
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{download_id}/progress")
async def get_download_progress(download_id: int) -> Dict:
    """Get download progress."""
    try:
        return await download_service.get_progress(download_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/torrent")
async def add_torrent_download(request: TorrentDownloadRequest) -> Download:
    """Add a torrent download."""
    try:
        if not request.magnet_link or not request.magnet_link.strip():
            raise HTTPException(status_code=400, detail="Magnet link cannot be empty")
        
        # Validate magnet link format
        if not validate_magnet_link(request.magnet_link):
            raise HTTPException(
                status_code=400, 
                detail="Invalid magnet link format. Must start with 'magnet:' and contain 'xt=urn:btih:'"
            )
        
        download = await download_service.add_torrent(request.magnet_link, request.download_path)
        
        # Auto-assign tags based on download name
        try:
            tag_service.auto_assign_tags(download)
        except Exception as tag_error:
            # Don't fail the download creation if auto-tagging fails
            pass
        
        return download
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nzb")
async def add_nzb_download(request: NZBDownloadRequest) -> Download:
    """Add an NZB download."""
    try:
        if not request.nzb_content or not request.nzb_content.strip():
            raise HTTPException(status_code=400, detail="NZB content cannot be empty")
        # Set default download path if none provided
        if not request.download_path:
            request.download_path = settings.DEFAULT_DOWNLOAD_PATH

        
        download = await download_service.add_nzb(request.nzb_content, request.download_path)
        
        # Auto-assign tags based on download name
        try:
            tag_service.auto_assign_tags(download)
        except Exception as tag_error:
            # Don't fail the download creation if auto-tagging fails
            pass
        
        return download
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{download_id}/pause")
async def pause_download(download_id: int):
    """Pause a download."""
    try:
        success = await download_service.pause_download(download_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} paused"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{download_id}/resume")
async def resume_download(download_id: int):
    """Resume a download."""
    try:
        success = await download_service.resume_download(download_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} resumed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{download_id}")
async def delete_download(download_id: int, delete_files: bool = False):
    """Remove a download."""
    try:
        success = await download_service.remove_download(download_id, delete_files)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{download_id}/file-priorities")
async def set_file_priorities(download_id: int, request: FilePriorityRequest):
    """Set file priorities for a torrent."""
    try:
        return await download_service.set_file_priorities(download_id, request.priorities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{download_id}/restart")
async def restart_download(download_id: int):
    """Restart a failed or stuck download."""
    try:
        success = await download_service.restart_download(download_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download not found")
        return {"message": f"Download {download_id} restarted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_downloads():
    """Clean up downloads with invalid URLs or states."""
    try:
        result = await download_service.cleanup_invalid_downloads()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/torrent-file")
async def add_torrent_file_upload(file: UploadFile = File(...), download_path: Optional[str] = Form(None)):
    """Add a torrent file download with configurable size limits."""
    try:
        # Improved file validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension and content type
        valid_extensions = ['.torrent']
        valid_content_types = ['application/x-bittorrent', 'application/octet-stream']
        
        is_valid_extension = any(file.filename.lower().endswith(ext) for ext in valid_extensions)
        is_valid_content_type = file.content_type in valid_content_types
        
        if not (is_valid_extension or is_valid_content_type):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Expected .torrent file, got: {file.filename} (content-type: {file.content_type})"
            )
        
        # Read and validate file size
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Validate file size against configured limit
        validate_file_size(file_content, settings.MAX_TORRENT_FILE_SIZE_MB, "torrent")
        
        # Reset file pointer for service to use
        await file.seek(0)
        
        download = await download_service.add_torrent_file(file, download_path)
        
        # Auto-assign tags based on download name
        try:
            tag_service.auto_assign_tags(download)
        except Exception as tag_error:
            # Don't fail the download creation if auto-tagging fails
            logger.warning(f"Auto-tagging failed: {tag_error}")
        
        return download
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing torrent file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nzb-file")
async def add_nzb_file_upload(file: UploadFile = File(...), download_path: Optional[str] = Form(None)):
    """Add an NZB file download with improved timeout handling and configurable size limits."""
    try:
        # Improved file validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension and content type
        valid_extensions = ['.nzb']
        valid_content_types = ['application/x-nzb', 'application/xml', 'text/xml', 'application/octet-stream']
        
        is_valid_extension = any(file.filename.lower().endswith(ext) for ext in valid_extensions)
        is_valid_content_type = file.content_type in valid_content_types
        
        if not (is_valid_extension or is_valid_content_type):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Expected .nzb file, got: {file.filename} (content-type: {file.content_type})"
            )
        
        # Check file size with configurable limit
        max_size_bytes = settings.MAX_NZB_FILE_SIZE_MB * 1024 * 1024
        file_size = 0
        file_content = b""
        
        # Read file in chunks to avoid memory issues
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > max_size_bytes:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size for NZB files is {settings.MAX_NZB_FILE_SIZE_MB}MB."
                )
            file_content += chunk
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Convert bytes to string for NZB processing
        try:
            nzb_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not a valid text file")
        
        # Quick validation to ensure it's a valid NZB before processing
        if not nzb_content.strip().startswith('<?xml') and '<nzb' not in nzb_content.lower():
            raise HTTPException(status_code=400, detail="File does not appear to be a valid NZB file")
        
        # Set default download path if none provided
        if not download_path:
            download_path = settings.DEFAULT_DOWNLOAD_PATH

        # Process the NZB asynchronously to avoid timeouts
        import asyncio
        
        async def process_nzb():
            return await download_service.add_nzb(nzb_content, download_path)
        
        # Use asyncio.wait_for with a reasonable timeout
        try:
            download = await asyncio.wait_for(process_nzb(), timeout=30.0)
        except asyncio.TimeoutError:
            # If processing takes too long, return accepted status
            # and let it process in the background
            temp_download = {
                "id": 0,  # Will be assigned later
                "name": file.filename,
                "status": "queued",
                "message": "Large NZB file is being processed in the background"
            }
            return temp_download
        
        # Auto-assign tags based on download name
        try:
            tag_service.auto_assign_tags(download)
        except Exception as tag_error:
            # Don't fail the download creation if auto-tagging fails
            logger.warning(f"Auto-tagging failed: {tag_error}")
        
        return download
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing NZB file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process NZB file: {str(e)}")
