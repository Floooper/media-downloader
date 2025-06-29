from fastapi import APIRouter
from datetime import datetime
from ..services_manager import services

router = APIRouter(
    prefix="/api",
    tags=["status"]
)

@router.get("/status")
async def system_status():
    """Get system status including connection states"""
    try:
        # Get the NZB service to check Usenet connection
        nzb_service = services.get_nzb_downloader()
        torrent_service = services.get_torrent_downloader()
        
        # Test connections
        usenet_ok = nzb_service is not None
        torrent_ok = torrent_service is not None
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "connections": {
                "usenet": {
                    "status": "connected" if usenet_ok else "disconnected",
                    "error": None
                },
                "torrent": {
                    "status": "connected" if torrent_ok else "disconnected",
                    "error": None
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "connections": {
                "usenet": {"status": "unknown", "error": str(e)},
                "torrent": {"status": "unknown", "error": str(e)}
            }
        }
