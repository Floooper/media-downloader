from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time
from typing import Callable
from .config import settings
from .routes import downloads, queue, system, tags, websocket
from .database import check_db_connection

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Media Download Manager API",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.API_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add trusted host middleware if not in debug mode
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1"]
        )

    # Register routers
    app.include_router(downloads.router, prefix="/api")
    app.include_router(queue.router, prefix="/api")
    app.include_router(system.router, prefix="/api")
    app.include_router(tags.router, prefix="/api")
    app.include_router(websocket.router, prefix="/api")

    # Add middleware for request logging and timing
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log request details
        logger.info(
            f"Method={request.method} Path={request.url.path} "
            f"Status={response.status_code} Duration={duration:.3f}s"
        )
        
        return response

    # Add error handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

    # Add health check endpoint
    @app.get("/api/health")
    async def health_check():
        # Check database connection
        db_healthy = check_db_connection()
        
        # Get service status
        from .services_manager import services
        service_status = {
            "download_service": services.get_download_service() is not None,
            "queue_service": services.get_queue_manager() is not None,
            "nzb_service": services.get_nzb_downloader() is not None,
        }
        
        status_code = status.HTTP_200_OK if all([db_healthy, *service_status.values()]) else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if status_code == 200 else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "services": service_status,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT
            }
        )

    # Add startup event handler
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Initialize database
        from .database import init_db
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        # Initialize services
        try:
            from .services_manager import services
            download_service = services.get_download_service()
            queue_service = services.get_queue_manager()
            nzb_service = services.get_nzb_downloader()
            
            if not all([download_service, queue_service, nzb_service]):
                logger.warning("Some services failed to initialize")
            else:
                logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

    # Add shutdown event handler
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")
        # Add cleanup code here if needed

    return app

# Create the application instance
app = create_app()
