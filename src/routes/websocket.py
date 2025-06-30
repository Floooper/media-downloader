from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket_manager import manager
import logging

router = APIRouter()

@router.websocket("/ws/{download_id}")
async def websocket_endpoint(websocket: WebSocket, download_id: int):
    await manager.connect(websocket, download_id)
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Echo back any messages (optional)
            await manager.send_personal_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
