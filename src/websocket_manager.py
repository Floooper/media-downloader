from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._download_queues: Dict[int, asyncio.Queue] = {}
        
    async def connect(self, websocket: WebSocket, download_id: int = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if download_id:
            if download_id not in self._download_queues:
                self._download_queues[download_id] = asyncio.Queue()
            
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
                
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass
            
    async def broadcast_download_log(self, download_id: int, message: str, level: str = "INFO"):
        log_entry = {
            "download_id": download_id,
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if download_id in self._download_queues:
            await self._download_queues[download_id].put(log_entry)
            
        await self.broadcast(json.dumps(log_entry))
        
    def get_download_queue(self, download_id: int) -> asyncio.Queue:
        if download_id not in self._download_queues:
            self._download_queues[download_id] = asyncio.Queue()
        return self._download_queues[download_id]

class WebSocketLogHandler(logging.Handler):
    def __init__(self, connection_manager):
        super().__init__()
        self.connection_manager = connection_manager
        
    def emit(self, record):
        try:
            # Extract download_id from the record if available
            download_id = getattr(record, "download_id", None)
            if download_id:
                asyncio.create_task(
                    self.connection_manager.broadcast_download_log(
                        download_id=download_id,
                        message=self.format(record),
                        level=record.levelname
                    )
                )
        except Exception:
            self.handleError(record)

manager = ConnectionManager()
