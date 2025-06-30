from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
from .websocket_manager import manager, WebSocketLogHandler
from .settings import settings

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add WebSocket handler to root logger
ws_handler = WebSocketLogHandler(manager)
ws_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(ws_handler)

# Log config on startup
logger.info("Starting with configuration:")
logger.info(f"Usenet host: {settings.USENET_SERVER}")
logger.info(f"Usenet port: {settings.USENET_PORT}")
logger.info(f"Usenet SSL: {settings.USENET_SSL}")
logger.info(f"Usenet username: {settings.USENET_USERNAME}")
logger.info(f"Max connections: {settings.USENET_CONNECTIONS}")
logger.info(f"Downloads path: {settings.DEFAULT_DOWNLOAD_PATH}")

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from .routes import websocket, downloads, system, queue, tags

# Include routes
app.include_router(websocket.router)
app.include_router(downloads.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(queue.router, prefix="/api")
app.include_router(tags.router, prefix="/api")

# Get root directory for static files
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(root_dir, "frontend", "dist")

# Mount static files if the directory exists
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path) as f:
                return f.read()
        return "Frontend not built"
else:
    @app.get("/")
    async def read_root():
        return {"message": "API running, frontend not built"}

# Register WebSocket manager cleanup
@app.on_event("shutdown")
async def shutdown_event():
    # Close any open WebSocket connections
    for connection in manager.active_connections:
        await connection.close()
