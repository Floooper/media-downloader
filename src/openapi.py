from fastapi.openapi.utils import get_openapi
from .config import settings

def custom_openapi(app):
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        Media Download Manager API - A unified solution for managing media downloads.
        
        ## Features
        * Download management (NZB, Torrent)
        * Queue management
        * Tag-based organization
        * Real-time progress updates
        * Media manager integration
        
        ## Authentication
        Most endpoints require authentication. Use the Authorization header with a valid API token:
        ```
        Authorization: Bearer your-token-here
        ```
        
        ## Rate Limiting
        API requests are rate-limited to prevent abuse. The current limits are:
        * 100 requests per minute for authenticated users
        * 10 requests per minute for unauthenticated users
        
        ## WebSocket Support
        Real-time updates are available through WebSocket connections:
        * `/api/ws` - General updates
        * `/api/ws/downloads/{download_id}` - Specific download updates
        * `/api/ws/system` - System status updates
        
        ## Error Handling
        The API uses standard HTTP status codes and returns error details in the response body:
        ```json
        {
            "detail": "Error description"
        }
        ```
        """,
        routes=app.routes,
    )

    # Custom tags metadata
    openapi_schema["tags"] = [
        {
            "name": "downloads",
            "description": "Download management operations"
        },
        {
            "name": "queue",
            "description": "Queue management operations"
        },
        {
            "name": "tags",
            "description": "Tag management operations"
        },
        {
            "name": "system",
            "description": "System information and settings"
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket communication"
        }
    ]

    # Security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Add security requirement to all routes
    if "security" not in openapi_schema:
        openapi_schema["security"] = [{"bearerAuth": []}]

    # Add response examples
    openapi_schema["components"]["examples"] = {
        "Download": {
            "value": {
                "id": 1,
                "name": "Example Download",
                "status": "downloading",
                "progress": 45.5,
                "download_type": "torrent",
                "download_path": "/downloads/example",
                "speed": 1024000,
                "eta": "00:15:30",
                "tags": [
                    {
                        "id": 1,
                        "name": "movies",
                        "color": "#ff0000"
                    }
                ]
            }
        },
        "Tag": {
            "value": {
                "id": 1,
                "name": "movies",
                "color": "#ff0000",
                "tag_type": "custom",
                "destination_folder": "/media/movies",
                "auto_assign_pattern": ".*\\.mp4$"
            }
        },
        "QueueStats": {
            "value": {
                "total_items": 10,
                "active_downloads": 2,
                "queued_downloads": 5,
                "completed_downloads": 2,
                "failed_downloads": 1,
                "total_progress": 35.5,
                "average_speed": 1024000
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
