from fastapi import APIRouter, Depends, HTTPException
from ..models.tables import DownloadStatus, DownloadTable
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
import psutil
import logging
from typing import Dict, Any
from ..services_manager import services

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_usenet_status() -> Dict[str, Any]:
    """Get current Usenet connection status and metrics"""
    try:
        nzb_service = services.get_nzb_downloader()
        if not nzb_service:
            return {
                "connected": False,
                "max_connections": settings.USENET_MAX_CONNECTIONS,
                "active_connections": 0,
                "download_rate": 0
            }
            
        return {
            "connected": True,
            "max_connections": settings.USENET_MAX_CONNECTIONS,
            "active_connections": nzb_service.stats.get("active_connections", 0),
            "download_rate": nzb_service.stats.get("download_rate", 0)
        }
    except Exception as e:
        logger.error(f"Failed to get Usenet status: {e}")
        return {
            "connected": False,
            "max_connections": settings.USENET_MAX_CONNECTIONS,
            "active_connections": 0,
            "download_rate": 0
        }

async def get_system_metrics() -> Dict[str, float]:
    """Get system resource metrics"""
    try:
        # Get CPU usage with a 0.1 second interval
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Get disk usage for download directory
        download_path = settings.DOWNLOAD_PATH or "/"
        disk = psutil.disk_usage(download_path)
        
        return {
            "cpu_usage": cpu,
            "memory_usage": memory.percent,
            "memory_available": memory.available / (1024 * 1024),  # MB
            "disk_usage": disk.percent,
            "disk_free": disk.free / (1024 * 1024 * 1024)  # GB
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "memory_available": 0,
            "disk_usage": 0,
            "disk_free": 0
        }

@router.get("/system/status")
async def get_system_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive system status including downloads and resources"""
    try:
        # Get download counts with error handling
        try:
            downloads = db.query(DownloadTable).all()
            active = sum(1 for d in downloads if d.status == DownloadStatus.DOWNLOADING)
            queued = sum(1 for d in downloads if d.status == DownloadStatus.QUEUED)
            completed = sum(1 for d in downloads if d.status == DownloadStatus.COMPLETED)
            failed = sum(1 for d in downloads if d.status == DownloadStatus.FAILED)
        except Exception as e:
            logger.error(f"Failed to get download counts: {e}")
            active = queued = completed = failed = 0

        return {
            "usenet": await get_usenet_status(),
            "downloads": {
                "active": active,
                "queued": queued,
                "completed": completed,
                "failed": failed,
                "total": len(downloads) if 'downloads' in locals() else 0
            },
            "system": await get_system_metrics()
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system status"
        )

@router.get("/system/info")
async def get_system_info() -> Dict[str, Any]:
    """Get system version and operational status"""
    try:
        # Check core services
        download_service = services.get_download_service()
        queue_service = services.get_queue_manager()
        nzb_service = services.get_nzb_downloader()
        
        services_status = {
            "download_service": download_service is not None,
            "queue_service": queue_service is not None,
            "nzb_service": nzb_service is not None
        }
        
        operational = all(services_status.values())
        
        return {
            "version": settings.APP_VERSION,
            "status": "operational" if operational else "degraded",
            "services": services_status,
            "environment": settings.ENVIRONMENT,
            "settings": {
                "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS,
                "download_path": settings.DOWNLOAD_PATH,
                "usenet_enabled": bool(settings.USENET_SERVER),
                "torrent_enabled": settings.ENABLE_TORRENTS
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system information"
        )
