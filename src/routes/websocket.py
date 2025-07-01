import logging
import json
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from ..websocket_manager import manager
from ..models.schemas import DownloadProgress
from ..services_manager import services
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

class WebSocketMessage:
    """Base class for WebSocket messages"""
    def __init__(self, type: str, data: Dict[str, Any]):
        self.type = type
        self.data = data

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": settings.current_time
        })

class ProgressMessage(WebSocketMessage):
    """Download progress message"""
    def __init__(self, progress: DownloadProgress):
        super().__init__("progress", progress.model_dump())

class StatusMessage(WebSocketMessage):
    """System status message"""
    def __init__(self, status: Dict[str, Any]):
        super().__init__("status", status)

class ErrorMessage(WebSocketMessage):
    """Error message"""
    def __init__(self, error: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("error", {
            "message": error,
            "details": details or {}
        })

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial system status
        system_service = services.get_system_service()
        if system_service:
            status = await system_service.get_status()
            await websocket.send_text(StatusMessage(status).to_json())

        while True:
            try:
                # Wait for messages with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_HEARTBEAT_INTERVAL
                )
                
                try:
                    message = json.loads(data)
                    await process_message(websocket, message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")
                    await websocket.send_text(
                        ErrorMessage("Invalid JSON format").to_json()
                    )
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(
                    WebSocketMessage("heartbeat", {}).to_json()
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/downloads/{download_id}")
async def download_websocket(websocket: WebSocket, download_id: int):
    """WebSocket endpoint for specific download updates"""
    await manager.connect(websocket, download_id)
    
    try:
        download_service = services.get_download_service()
        if not download_service:
            await websocket.send_text(
                ErrorMessage("Download service unavailable").to_json()
            )
            return
            
        # Verify download exists
        download = await download_service.get_download(download_id)
        if not download:
            await websocket.send_text(
                ErrorMessage("Download not found").to_json()
            )
            return
            
        # Send initial progress
        progress = await download_service.get_progress(download_id)
        if progress:
            await websocket.send_text(
                ProgressMessage(progress).to_json()
            )
            
        # Listen for download updates
        queue = manager.get_download_queue(download_id)
        while True:
            try:
                # Wait for updates with timeout
                update = await asyncio.wait_for(
                    queue.get(),
                    timeout=settings.WS_HEARTBEAT_INTERVAL
                )
                
                await websocket.send_text(json.dumps(update))
                queue.task_done()
                
            except asyncio.TimeoutError:
                # Send heartbeat and check download still exists
                download = await download_service.get_download(download_id)
                if not download:
                    await websocket.send_text(
                        ErrorMessage("Download no longer exists").to_json()
                    )
                    break
                    
                await websocket.send_text(
                    WebSocketMessage("heartbeat", {}).to_json()
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected from download {download_id}")
    except Exception as e:
        logger.error(f"Download WebSocket error: {e}")
        manager.disconnect(websocket)

async def process_message(websocket: WebSocket, message: Dict[str, Any]):
    """Process incoming WebSocket messages"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "subscribe":
            # Handle subscription requests
            download_id = data.get("download_id")
            if download_id:
                await manager.subscribe_to_download(websocket, download_id)
                await websocket.send_text(
                    WebSocketMessage("subscribed", {"download_id": download_id}).to_json()
                )
                
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            download_id = data.get("download_id")
            if download_id:
                await manager.unsubscribe_from_download(websocket, download_id)
                await websocket.send_text(
                    WebSocketMessage("unsubscribed", {"download_id": download_id}).to_json()
                )
                
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket.send_text(
                ErrorMessage("Unknown message type").to_json()
            )
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await websocket.send_text(
            ErrorMessage("Error processing message").to_json()
        )

@router.websocket("/ws/system")
async def system_websocket(websocket: WebSocket):
    """WebSocket endpoint for system status updates"""
    await manager.connect(websocket)
    
    try:
        system_service = services.get_system_service()
        if not system_service:
            await websocket.send_text(
                ErrorMessage("System service unavailable").to_json()
            )
            return
            
        while True:
            try:
                # Get system status every interval
                status = await system_service.get_status()
                await websocket.send_text(
                    StatusMessage(status).to_json()
                )
                
                await asyncio.sleep(settings.SYSTEM_STATUS_INTERVAL)
                
            except asyncio.CancelledError:
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from system updates")
    except Exception as e:
        logger.error(f"System WebSocket error: {e}")
        manager.disconnect(websocket)
