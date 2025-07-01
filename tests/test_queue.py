import pytest
from fastapi.testclient import TestClient
from ..src.models.enums import DownloadStatus, DownloadType

def test_get_queue(client, sample_download):
    """Test getting download queue"""
    response = client.get("/api/queue/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == sample_download.id

def test_get_queue_with_status_filter(client, db_session):
    """Test getting queue with status filter"""
    # Create downloads with different statuses
    downloads = [
        Download(
            name=f"download_{status.value}",
            status=status,
            download_type=DownloadType.TORRENT
        )
        for status in DownloadStatus
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    response = client.get(
        "/api/queue/",
        params={"status": [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    statuses = [d["status"] for d in data]
    assert all(s in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING] for s in statuses)

def test_reorder_queue(client, db_session):
    """Test reordering the queue"""
    # Create multiple downloads
    downloads = [
        Download(name=f"download_{i}", download_type=DownloadType.TORRENT)
        for i in range(3)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    # Reorder downloads
    new_order = [
        {"download_id": d.id, "position": i}
        for i, d in enumerate(reversed(downloads))
    ]
    
    response = client.post("/api/queue/reorder", json=new_order)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["position"] == 0
    assert data[0]["download_id"] == downloads[-1].id

def test_clear_queue(client, db_session):
    """Test clearing the queue"""
    # Create multiple downloads
    downloads = [
        Download(
            name=f"download_{i}",
            status=DownloadStatus.QUEUED,
            download_type=DownloadType.TORRENT
        )
        for i in range(3)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    response = client.post("/api/queue/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["cleared_items"] == 3
    
    # Verify queue is empty
    response = client.get("/api/queue/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_get_queue_stats(client, db_session):
    """Test getting queue statistics"""
    # Create downloads with different statuses
    downloads = [
        Download(
            name=f"download_{status.value}",
            status=status,
            download_type=DownloadType.TORRENT,
            progress=50.0 if status == DownloadStatus.DOWNLOADING else 0.0,
            speed=1024 if status == DownloadStatus.DOWNLOADING else 0.0
        )
        for status in DownloadStatus
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    response = client.get("/api/queue/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == len(DownloadStatus)
    assert data["active_downloads"] == 1  # DOWNLOADING status
    assert data["queued_downloads"] == 1  # QUEUED status
    assert data["completed_downloads"] == 1  # COMPLETED status
    assert data["failed_downloads"] == 1  # FAILED status
    assert data["total_progress"] > 0
    assert data["average_speed"] > 0

def test_move_in_queue(client, db_session):
    """Test moving a download in the queue"""
    # Create multiple downloads
    downloads = [
        Download(name=f"download_{i}", download_type=DownloadType.TORRENT)
        for i in range(3)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    # Move last download to first position
    response = client.post(
        f"/api/queue/{downloads[-1].id}/move",
        params={"position": 0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["position"] == 0
    assert data["download_id"] == downloads[-1].id

def test_prioritize_download(client, db_session):
    """Test prioritizing a download"""
    # Create multiple downloads
    downloads = [
        Download(name=f"download_{i}", download_type=DownloadType.TORRENT)
        for i in range(3)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    # Prioritize last download
    response = client.post(f"/api/queue/{downloads[-1].id}/prioritize")
    assert response.status_code == 200
    
    # Verify download is first in queue
    response = client.get("/api/queue/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == downloads[-1].id

def test_optimize_queue(client, db_session):
    """Test optimizing the queue"""
    # Create downloads with various characteristics
    downloads = [
        Download(
            name="large_download",
            download_type=DownloadType.TORRENT,
            file_size=1024*1024*1024  # 1GB
        ),
        Download(
            name="small_download",
            download_type=DownloadType.TORRENT,
            file_size=1024*1024  # 1MB
        ),
        Download(
            name="medium_download",
            download_type=DownloadType.TORRENT,
            file_size=1024*1024*100  # 100MB
        )
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    response = client.post("/api/queue/optimize")
    assert response.status_code == 200
    data = response.json()
    assert "queue" in data
    assert len(data["queue"]) == 3
