from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketError(Exception):
    """Base exception for WebSocket errors"""
    pass

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._download_queues: Dict[int, asyncio.Queue] = {}
        self._connection_retries: Dict[WebSocket, int] = {}
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1.0  # seconds
        
    async def connect(self, websocket: WebSocket, download_id: Optional[int] = None) -> bool:
        """Connect a WebSocket client with retry logic"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self._connection_retries[websocket] = 0
            
            if download_id is not None:
                if download_id not in self._download_queues:
                    self._download_queues[download_id] = asyncio.Queue()
                    
            logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            return False
            
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                self._connection_retries.pop(websocket, None)
                logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
                
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients with retry logic"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                self._connection_retries[connection] = 0  # Reset retry count on success
                
            except WebSocketDisconnect:
                disconnected.append(connection)
                logger.info(f"Client disconnected during broadcast")
                
            except Exception as e:
                retries = self._connection_retries.get(connection, 0)
                if retries < self.MAX_RETRIES:
                    self._connection_retries[connection] = retries + 1
                    logger.warning(f"Broadcast failed (attempt {retries + 1}/{self.MAX_RETRIES}): {e}")
                    await asyncio.sleep(self.RETRY_DELAY)
                    try:
                        await connection.send_text(message)
                    except Exception:
                        disconnected.append(connection)
                else:
                    logger.error(f"Broadcast failed after {self.MAX_RETRIES} attempts")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
                
    async def send_personal_message(self, message: str, websocket: WebSocket) -> bool:
        """Send message to specific client with retry logic"""
        try:
            await websocket.send_text(message)
            self._connection_retries[websocket] = 0  # Reset retry count on success
            return True
            
        except WebSocketDisconnect:
            self.disconnect(websocket)
            logger.info("Client disconnected during personal message")
            return False
            
        except Exception as e:
            retries = self._connection_retries.get(websocket, 0)
            if retries < self.MAX_RETRIES:
                self._connection_retries[websocket] = retries + 1
                logger.warning(f"Personal message failed (attempt {retries + 1}/{self.MAX_RETRIES}): {e}")
                await asyncio.sleep(self.RETRY_DELAY)
                try:
                    await websocket.send_text(message)
                    return True
                except Exception:
                    self.disconnect(websocket)
                    return False
            else:
                logger.error(f"Personal message failed after {self.MAX_RETRIES} attempts")
                self.disconnect(websocket)
                return False
            
    async def broadcast_download_log(self, download_id: int, message: str, level: str = "INFO"):
        """Broadcast download log with queue management"""
        try:
            log_entry = {
                "download_id": download_id,
                "message": message,
                "level": level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to download queue if it exists
            if download_id in self._download_queues:
                try:
                    await self._download_queues[download_id].put(log_entry)
                except asyncio.QueueFull:
                    logger.warning(f"Download queue full for download_id {download_id}")
                    # Remove oldest item and try again
                    try:
                        self._download_queues[download_id].get_nowait()
                        await self._download_queues[download_id].put(log_entry)
                    except Exception as e:
                        logger.error(f"Failed to manage queue for download_id {download_id}: {e}")
            
            # Broadcast to all connections
            await self.broadcast(json.dumps(log_entry))
            
        except Exception as e:
            logger.error(f"Error broadcasting download log: {e}")
        
    def get_download_queue(self, download_id: int) -> asyncio.Queue:
        """Get or create download queue"""
        if download_id not in self._download_queues:
            self._download_queues[download_id] = asyncio.Queue(maxsize=1000)  # Limit queue size
        return self._download_queues[download_id]

class WebSocketLogHandler(logging.Handler):
    """Custom logging handler for WebSocket broadcasts"""
    def __init__(self, connection_manager: ConnectionManager):
        super().__init__()
        self.connection_manager = connection_manager
        
    def emit(self, record: logging.LogRecord):
        """Emit a log record to WebSocket clients"""
        try:
            # Extract download_id from the record if available
            download_id = getattr(record, "download_id", None)
            if download_id is not None:
                asyncio.create_task(
                    self.connection_manager.broadcast_download_log(
                        download_id=download_id,
                        message=self.format(record),
                        level=record.levelname
                    )
                )
        except Exception as e:
            logger.error(f"Error in WebSocket log handler: {e}")
            self.handleError(record)

# Global connection manager instance
manager = ConnectionManager()
