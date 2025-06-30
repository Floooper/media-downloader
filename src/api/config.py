from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..settings import settings, save_settings

router = APIRouter(prefix="/api/config", tags=["config"])

class UsenetConfig(BaseModel):
    server: str
    port: int
    use_ssl: bool
    username: str
    password: str
    max_connections: int = 10
    retention_days: int = 1500
    download_rate_limit: Optional[int] = None
    max_retries: int = 3

class SystemConfig(BaseModel):
    usenet: UsenetConfig
    default_download_path: str
    max_concurrent_downloads: int
    api_host: str
    api_port: int
    log_level: str

@router.get("/usenet")
async def get_usenet_config():
    """Get current Usenet configuration."""
    return {
        "server": settings.USENET_SERVER,
        "port": settings.USENET_PORT,
        "use_ssl": settings.USENET_SSL,
        "username": settings.USENET_USERNAME,
        "password": "***" if settings.USENET_PASSWORD else "",
        "max_connections": settings.USENET_CONNECTIONS,
        "retention_days": settings.USENET_RETENTION,
        "download_rate_limit": settings.USENET_RATE_LIMIT,
        "max_retries": settings.USENET_MAX_RETRIES
    }

@router.put("/usenet")
async def update_usenet_config(config: UsenetConfig):
    """Update Usenet configuration."""
    try:
        # Create settings dict
        settings_dict = {
            "USENET_SERVER": config.server,
            "USENET_PORT": str(config.port),
            "USENET_SSL": str(config.use_ssl),
            "USENET_USERNAME": config.username,
            "USENET_CONNECTIONS": str(config.max_connections),
            "USENET_RETENTION": str(config.retention_days),
            "USENET_RATE_LIMIT": str(config.download_rate_limit) if config.download_rate_limit else "",
            "USENET_MAX_RETRIES": str(config.max_retries)
        }
        
        # Only update password if it's not masked
        if config.password != "***":
            settings_dict["USENET_PASSWORD"] = config.password
        
        # Save settings
        save_settings(settings_dict)
        
        # Update runtime settings
        settings.USENET_SERVER = config.server
        settings.USENET_PORT = config.port
        settings.USENET_SSL = config.use_ssl
        settings.USENET_USERNAME = config.username
        if config.password != "***":
            settings.USENET_PASSWORD = config.password
        settings.USENET_CONNECTIONS = config.max_connections
        settings.USENET_RETENTION = config.retention_days
        settings.USENET_RATE_LIMIT = config.download_rate_limit
        settings.USENET_MAX_RETRIES = config.max_retries
        
        return {"message": "Usenet configuration updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

@router.get("/")
async def get_config():
    """Get basic configuration."""
    return {
        "api_host": settings.API_HOST,
        "api_port": settings.API_PORT,
        "default_download_path": settings.DEFAULT_DOWNLOAD_PATH,
        "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS
    }

@router.put("/")
async def update_config(config_data: dict):
    """Update basic configuration."""
    try:
        settings_dict = {
            "API_HOST": config_data.get("api_host", settings.API_HOST),
            "API_PORT": str(config_data.get("api_port", settings.API_PORT)),
            "DEFAULT_DOWNLOAD_PATH": config_data.get("default_download_path", settings.DEFAULT_DOWNLOAD_PATH),
            "MAX_CONCURRENT_DOWNLOADS": str(config_data.get("max_concurrent_downloads", settings.MAX_CONCURRENT_DOWNLOADS))
        }
        
        save_settings(settings_dict)
        
        # Update runtime settings
        for key, value in config_data.items():
            setattr(settings, key.upper(), value)
            
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

@router.get("/system")
async def get_system_config():
    """Get all system configuration."""
    return {
        "usenet": {
            "server": settings.USENET_SERVER,
            "port": settings.USENET_PORT,
            "use_ssl": settings.USENET_SSL,
            "username": settings.USENET_USERNAME,
            "password": "***" if settings.USENET_PASSWORD else "",
            "max_connections": settings.USENET_CONNECTIONS,
            "retention_days": settings.USENET_RETENTION,
            "download_rate_limit": settings.USENET_RATE_LIMIT,
            "max_retries": settings.USENET_MAX_RETRIES
        },
        "default_download_path": settings.DEFAULT_DOWNLOAD_PATH,
        "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS,
        "api_host": settings.API_HOST,
        "api_port": settings.API_PORT,
        "log_level": settings.LOG_LEVEL
    }

@router.post("/test-connection")
async def test_connection(config: UsenetConfig):
    """Test Usenet server connection with provided configuration."""
    try:
        # Import here to avoid circular imports
        from ..services.nzb_service import NZBService
        
        # Create a test config
        test_config = {
            "host": config.server,
            "port": config.port,
            "ssl": config.use_ssl,
            "username": config.username,
            "password": config.password if config.password != "***" else settings.USENET_PASSWORD,
            "max_connections": 1  # Use just 1 connection for testing
        }
        
        # Create service instance
        service = NZBService(test_config)
        
        # Test connection
        conn = service._get_connection()
        conn.quit()
        
        return {"success": True, "message": "Connection successful"}
        
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}
