from fastapi import APIRouter
from ..config import config
from typing import Dict, Any

router = APIRouter()

@router.get("/system/info")
async def get_system_info():
    return {
        "status": "operational",
        "version": "1.0.0"
    }

@router.get("/system/config")
async def get_config():
    """Get all configuration except sensitive values"""
    safe_config = {
        "usenet": {
            "host": config.get("usenet.host"),
            "port": config.get("usenet.port"),
            "ssl": config.get("usenet.ssl"),
            "username": config.get("usenet.username"),
            "connections": config.get("usenet.connections"),
            "retention": config.get("usenet.retention")
        },
        "downloads": {
            "path": config.get("downloads.path"),
            "temp_path": config.get("downloads.temp_path"),
            "completed_path": config.get("downloads.completed_path"),
            "failed_path": config.get("downloads.failed_path")
        },
        "web": {
            "host": config.get("web.host"),
            "port": config.get("web.port")
        }
    }
    return safe_config

@router.get("/system/usenet")
async def get_usenet_config():
    """Get Usenet configuration except password"""
    return {
        "host": config.get("usenet.host"),
        "port": config.get("usenet.port"),
        "ssl": config.get("usenet.ssl"),
        "username": config.get("usenet.username"),
        "connections": config.get("usenet.connections"),
        "retention": config.get("usenet.retention")
    }
