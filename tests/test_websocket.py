import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from ..src.models.enums import DownloadStatus, DownloadType

def test_websocket_connection(client):
    """Test basic WebSocket connection"""
    with client.websocket_connect("/api/ws") as websocket:
        # Should receive initial system status
        data = json.loads(websocket.receive_text())
        assert data["type"] == "status"
        assert "data" in data

def test_download_websocket(client, sample_download):
    """Test WebSocket connection for specific download"""
    with client.websocket_connect(f"/api/ws/downloads/{sample_download.id}") as websocket:
        # Should receive initial progress
        data = json.loads(websocket.receive_text())
        assert data["type"] == "progress"
        assert data["data"]["id"] == sample_download.id

def test_websocket_heartbeat(client):
    """Test WebSocket heartbeat mechanism"""
    with client.websocket_connect("/api/ws") as websocket:
        # Wait for heartbeat
        data = json.loads(websocket.receive_text())
        assert data["type"] == "heartbeat"

def test_download_updates(client, sample_download, db_session):
    """Test receiving download updates via WebSocket"""
    with client.websocket_connect(f"/api/ws/downloads/{sample_download.id}") as websocket:
        # Update download status
        sample_download.status = DownloadStatus.DOWNLOADING
        sample_download.progress = 50.0
        db_session.commit()
        
        # Should receive update
        data = json.loads(websocket.receive_text())
        assert data["type"] == "progress"
        assert data["data"]["progress"] == 50.0
        assert data["data"]["status"] == DownloadStatus.DOWNLOADING

def test_system_websocket(client):
    """Test system status WebSocket endpoint"""
    with client.websocket_connect("/api/ws/system") as websocket:
        # Should receive system status updates
        data = json.loads(websocket.receive_text())
        assert data["type"] == "status"
        assert "cpu_usage" in data["data"]
        assert "memory_usage" in data["data"]
        assert "disk_usage" in data["data"]

def test_websocket_subscription(client, sample_download):
    """Test WebSocket subscription mechanism"""
    with client.websocket_connect("/api/ws") as websocket:
        # Subscribe to download updates
        websocket.send_text(json.dumps({
            "type": "subscribe",
            "data": {"download_id": sample_download.id}
        }))
        
        # Should receive confirmation
        data = json.loads(websocket.receive_text())
        assert data["type"] == "subscribed"
        assert data["data"]["download_id"] == sample_download.id

def test_websocket_unsubscription(client, sample_download):
    """Test WebSocket unsubscription mechanism"""
    with client.websocket_connect("/api/ws") as websocket:
        # Subscribe then unsubscribe
        websocket.send_text(json.dumps({
            "type": "subscribe",
            "data": {"download_id": sample_download.id}
        }))
        websocket.receive_text()  # Subscription confirmation
        
        websocket.send_text(json.dumps({
            "type": "unsubscribe",
            "data": {"download_id": sample_download.id}
        }))
        
        # Should receive confirmation
        data = json.loads(websocket.receive_text())
        assert data["type"] == "unsubscribed"
        assert data["data"]["download_id"] == sample_download.id

def test_invalid_message_format(client):
    """Test handling of invalid WebSocket messages"""
    with client.websocket_connect("/api/ws") as websocket:
        # Send invalid JSON
        websocket.send_text("invalid json")
        
        # Should receive error
        data = json.loads(websocket.receive_text())
        assert data["type"] == "error"
        assert "Invalid JSON format" in data["data"]["message"]

def test_unknown_message_type(client):
    """Test handling of unknown message types"""
    with client.websocket_connect("/api/ws") as websocket:
        # Send unknown message type
        websocket.send_text(json.dumps({
            "type": "unknown",
            "data": {}
        }))
        
        # Should receive error
        data = json.loads(websocket.receive_text())
        assert data["type"] == "error"
        assert "Unknown message type" in data["data"]["message"]

def test_download_not_found(client):
    """Test WebSocket connection for non-existent download"""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/ws/downloads/99999") as websocket:
            data = json.loads(websocket.receive_text())
            assert data["type"] == "error"
            assert "Download not found" in data["data"]["message"]

def test_concurrent_connections(client, sample_download):
    """Test multiple concurrent WebSocket connections"""
    with client.websocket_connect("/api/ws") as ws1, \
         client.websocket_connect("/api/ws") as ws2:
        # Both should receive system status
        data1 = json.loads(ws1.receive_text())
        data2 = json.loads(ws2.receive_text())
        assert data1["type"] == "status"
        assert data2["type"] == "status"

@pytest.mark.asyncio
async def test_websocket_queue_limit(client):
    """Test WebSocket message queue size limit"""
    with client.websocket_connect("/api/ws") as websocket:
        # Generate many messages quickly
        for i in range(150):  # More than queue size
            websocket.send_text(json.dumps({
                "type": "subscribe",
                "data": {"download_id": i}
            }))
            
        # Should still receive messages without errors
        for _ in range(5):  # Check a few messages
            data = json.loads(websocket.receive_text())
            assert data["type"] in ["subscribed", "error"]
