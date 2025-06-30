from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
from ..services.media_manager import MediaManagerIntegration, MediaManagerType
from ..config import settings

router = APIRouter(prefix="/api/media-managers", tags=["media-managers"])
media_manager = MediaManagerIntegration()

class ManagerConfig(BaseModel):
    url: str
    api_key: str
    enabled: bool = True
    auto_import: bool = True
    category_mappings: Optional[Dict[str, str]] = None

class ManagerStatus(BaseModel):
    type: MediaManagerType
    connected: bool
    version: Optional[str] = None
    health: str = "unknown"
    last_checked: Optional[str] = None

@router.get("/types")
def get_manager_types() -> List[str]:
    """Get available media manager types."""
    return [t.value for t in MediaManagerType]

@router.get("/discover")
async def discover_managers() -> List[Dict]:
    """Auto-discover media managers on the network."""
    try:
        return await media_manager.discover_managers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{manager_type}/test")
async def test_connection(manager_type: MediaManagerType, config: ManagerConfig) -> Dict:
    """Test connection to a media manager."""
    try:
        result = await media_manager.test_connection(
            manager_type,
            config.url,
            config.api_key
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{manager_type}/status")
async def get_status(manager_type: MediaManagerType) -> ManagerStatus:
    """Get current status of a media manager."""
    try:
        return await media_manager.get_status(manager_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{manager_type}/config")
async def save_config(manager_type: MediaManagerType, config: ManagerConfig) -> Dict:
    """Save configuration for a media manager."""
    try:
        await media_manager.save_config(manager_type, config.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{manager_type}/config")
async def get_config(manager_type: MediaManagerType) -> ManagerConfig:
    """Get configuration for a media manager."""
    try:
        config = await media_manager.get_config(manager_type)
        return ManagerConfig(**config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{manager_type}/tags")
async def get_tags(manager_type: MediaManagerType) -> List[Dict]:
    """Get available tags from a media manager."""
    try:
        return await media_manager.get_tags(manager_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{manager_type}/health-check")
async def trigger_health_check(
    manager_type: MediaManagerType,
    background_tasks: BackgroundTasks
) -> Dict:
    """Trigger a health check for a media manager."""
    try:
        background_tasks.add_task(media_manager.check_health, manager_type)
        return {"status": "Health check initiated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{manager_type}/categories")
async def get_categories(manager_type: MediaManagerType) -> List[Dict]:
    """Get download categories for a media manager."""
    try:
        return await media_manager.get_categories(manager_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{manager_type}/root-folders")
async def get_root_folders(manager_type: MediaManagerType) -> List[Dict]:
    """Get root folders for a media manager."""
    try:
        return await media_manager.get_root_folders(manager_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{manager_type}/quality-profiles")
async def get_quality_profiles(manager_type: MediaManagerType) -> List[Dict]:
    """Get quality profiles for a media manager."""
    try:
        return await media_manager.get_quality_profiles(manager_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{manager_type}/register")
async def register_downloader(manager_type: MediaManagerType, config: ManagerConfig) -> Dict:
    """Register this application as a download client with a media manager."""
    try:
        # Temporarily save the config for this registration attempt
        await media_manager.save_config(manager_type, config.dict())
        
        success = await media_manager.register_downloader(manager_type)
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register with {manager_type.value}"
            )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{manager_type}/notify-complete")
async def notify_download_complete(
    manager_type: MediaManagerType,
    path: str
) -> Dict:
    """Notify media manager of a completed download."""
    try:
        success = await media_manager.notify_download_complete(manager_type, path)
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to notify {manager_type.value}"
            )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


