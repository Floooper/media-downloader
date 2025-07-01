import pytest
from fastapi.testclient import TestClient
from ..src.models.enums import DownloadStatus, DownloadType

def test_list_downloads(client, sample_download):
    """Test listing downloads endpoint"""
    response = client.get("/api/downloads/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Test Download"

def test_list_downloads_with_filters(client, sample_download):
    """Test listing downloads with filters"""
    response = client.get(
        "/api/downloads/",
        params={
            "status": ["QUEUED"],
            "download_type": ["TORRENT"],
            "search": "Test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Download"

def test_upload_nzb_invalid_file(client):
    """Test uploading invalid NZB file"""
    response = client.post(
        "/api/downloads/nzb",
        files={"file": ("test.txt", b"invalid content")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_add_magnet_invalid_link(client):
    """Test adding invalid magnet link"""
    response = client.post(
        "/api/downloads/magnet",
        params={"magnet_link": "invalid"}
    )
    assert response.status_code == 400

def test_pause_download(client, sample_download):
    """Test pausing a download"""
    response = client.post(f"/api/downloads/{sample_download.id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DownloadStatus.PAUSED

def test_resume_download(client, sample_download):
    """Test resuming a download"""
    # First pause the download
    client.post(f"/api/downloads/{sample_download.id}/pause")
    
    response = client.post(f"/api/downloads/{sample_download.id}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == DownloadStatus.DOWNLOADING

def test_delete_download(client, sample_download):
    """Test deleting a download"""
    response = client.delete(f"/api/downloads/{sample_download.id}")
    assert response.status_code == 200
    
    # Verify download is deleted
    response = client.get(f"/api/downloads/{sample_download.id}")
    assert response.status_code == 404

def test_update_download(client, sample_download):
    """Test updating a download"""
    update_data = {
        "name": "Updated Download",
        "download_path": "/new/path"
    }
    response = client.patch(
        f"/api/downloads/{sample_download.id}",
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Download"
    assert data["download_path"] == "/new/path"

def test_get_download_progress(client, sample_download):
    """Test getting download progress"""
    response = client.get(f"/api/downloads/{sample_download.id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert "progress" in data
    assert "speed" in data
    assert "eta" in data

def test_invalid_download_id(client):
    """Test operations with invalid download ID"""
    invalid_id = 9999
    endpoints = [
        f"/api/downloads/{invalid_id}",
        f"/api/downloads/{invalid_id}/pause",
        f"/api/downloads/{invalid_id}/resume",
        f"/api/downloads/{invalid_id}/progress"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
