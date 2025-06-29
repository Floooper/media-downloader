from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import List
import logging
import traceback
import re
from .models.tables import DownloadTable as Download
from sqlalchemy.orm import Session
from .api.downloads import router as downloads_router
from .api.queue import router as queue_router
from .api.tags import router as tags_router
from .api.media_managers import router as media_managers_router
from .api.status import router as status_router
from .api.transmission import router as transmission_router
from .api.config import router as config_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Media Downloader",
    description="A unified application for downloading media",
    version="0.1.0"
)

# Custom CORS middleware to handle Docker networks dynamically
class CustomCORSMiddleware:
    def __init__(self, app, allow_credentials=True, allow_methods=None, allow_headers=None):
        self.app = app
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        
    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        allowed_patterns = [
            r"^http://localhost:5173$",
            r"^http://127\.0\.0\.1:5173$",
            r"^http://5\.39\.70\.40:5173$",
            r"^http://172\.\d+\.\d+\.\d+:5173$",  # Any Docker 172.x.x.x network
            r"^http://0\.0\.0\.0:5173$",
        ]
        
        for pattern in allowed_patterns:
            if re.match(pattern, origin):
                return True
        return False

# Use CORS middleware with wildcard to fix redirect issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins to fix CORS redirect issue
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
app.include_router(status_router)
)

# Include all routers
app.include_router(downloads_router)
app.include_router(queue_router)
app.include_router(tags_router)
app.include_router(media_managers_router)
app.include_router(transmission_router)
app.include_router(config_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/system/health")
async def api_health_check():
    """API health check endpoint."""
    from datetime import datetime
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "downloads": "running",
            "queue": "running", 
            "tags": "running"
        }
    }
@app.get("/api/system/info")
async def get_system_info():
    """Get system information."""
    import psutil
    import time
    from datetime import datetime, timedelta
    from .config import settings
    
    # Calculate uptime (simplified - would need process start time in real app)
    uptime_seconds = time.time() % (24 * 3600)  # Mock uptime for demo
    uptime_delta = timedelta(seconds=uptime_seconds)
    uptime_str = f"{uptime_delta.seconds // 3600} hours {(uptime_delta.seconds % 3600) // 60} minutes"
    
    return {
        "version": "0.1.0",
        "uptime": uptime_str,
        "api_host": settings.API_HOST or "localhost",
        "api_port": settings.API_PORT or 8000,
        "download_clients": {
            "transmission_url": f"http://{settings.API_HOST or 'localhost'}:{settings.API_PORT or 8000}/api/transmission/rpc",
            "config_endpoint": f"http://{settings.API_HOST or 'localhost'}:{settings.API_PORT or 8000}/api/transmission/client-config"
        },
        "supported_formats": ["Torrent", "Magnet Links", "NZB"],
        "active_connections": 3,  # Would be dynamic in real app
        "memory_usage": {
            "used_mb": round(psutil.virtual_memory().used / 1024 / 1024, 1),
            "total_mb": round(psutil.virtual_memory().total / 1024 / 1024, 1),
            "percent": psutil.virtual_memory().percent
        },
        "cpu_usage": psutil.cpu_percent(interval=1),
        "disk_usage": {
            "used_gb": round(psutil.disk_usage('/').used / 1024 / 1024 / 1024, 1),
            "total_gb": round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 1),
            "percent": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 1)
        }
    }

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    error_id = id(exc)
    logger.error(
        f"Unhandled exception {error_id}: {str(exc)}\n"
        f"Request: {request.method} {request.url}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "error_id": error_id,
            "request_url": str(request.url)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with better logging."""
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}\n"
        f"Request: {request.method} {request.url}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_url": str(request.url)
        }
    )


# Simple backwards compatibility routes for external tools
@app.get("/system/info")
async def system_info_compat():
    """Backwards compatibility route for /system/info -> /api/system/info"""
    return await get_system_info()

@app.get("/downloads")
@app.get("/downloads/")
async def downloads_compat():
    """Backwards compatibility route for /downloads -> /api/downloads/"""
    return {"message": "Downloads endpoint moved", "new_endpoint": "/api/downloads/", "redirect": True}

@app.get("/config")
async def config_compat():
    """Backwards compatibility route for /config -> /api/config"""
    return {"message": "Config endpoint moved", "new_endpoint": "/api/config/", "redirect": True}

@app.get("/tags/")
async def tags_compat():
    """Backwards compatibility route for /tags/ -> /api/tags/"""
    return {"message": "Tags endpoint moved", "new_endpoint": "/api/tags/", "redirect": True}

@app.api_route("/downloads/nzb-file", methods=["GET", "POST"])
async def nzb_file_compat():
    """Backwards compatibility route for NZB uploads"""
    return {"message": "NZB upload endpoint moved", "new_endpoint": "/api/downloads/nzb-file", "redirect": True}

if __name__ == "__main__":
    import uvicorn
    from .config import settings
    
    # Initialize services during startup
    logger.info("🚀 Starting Media Downloader API server...")
    
    # Start the server
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST or "0.0.0.0",
        port=settings.API_PORT or 8000,
        reload=False,  # Set to False for production
        log_level="info",
        timeout_keep_alive=30
    )

# Mount static files LAST to avoid interfering with API routes
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

@app.get("/status")
async def status_compat():
    """Backwards compatibility route for /status -> /api/status"""
    from .api.status import system_status
    return await system_status()
