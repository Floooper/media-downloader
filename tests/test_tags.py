import pytest
from fastapi.testclient import TestClient
from ..src.models.enums import TagType

def test_list_tags(client, sample_tag):
    """Test listing tags endpoint"""
    response = client.get("/api/tags/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Test Tag"

def test_list_tags_with_filter(client, sample_tag):
    """Test listing tags with type filter"""
    response = client.get("/api/tags/", params={"type": "CUSTOM"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tag_type"] == TagType.CUSTOM

def test_create_tag(client):
    """Test creating a new tag"""
    tag_data = {
        "name": "New Tag",
        "color": "#00ff00",
        "tag_type": TagType.CUSTOM
    }
    response = client.post("/api/tags/", json=tag_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Tag"
    assert data["color"] == "#00ff00"

def test_create_duplicate_tag(client, sample_tag):
    """Test creating a tag with duplicate name"""
    tag_data = {
        "name": "Test Tag",  # Same name as sample_tag
        "color": "#00ff00",
        "tag_type": TagType.CUSTOM
    }
    response = client.post("/api/tags/", json=tag_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

def test_update_tag(client, sample_tag):
    """Test updating a tag"""
    update_data = {
        "name": "Updated Tag",
        "color": "#0000ff"
    }
    response = client.put(f"/api/tags/{sample_tag.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Tag"
    assert data["color"] == "#0000ff"

def test_delete_tag(client, sample_tag):
    """Test deleting a tag"""
    response = client.delete(f"/api/tags/{sample_tag.id}")
    assert response.status_code == 200
    
    # Verify tag is deleted
    response = client.get(f"/api/tags/{sample_tag.id}")
    assert response.status_code == 404

def test_delete_system_tag(client, db_session):
    """Test attempting to delete a system tag"""
    system_tag = Tag(
        name="System Tag",
        color="#ff0000",
        tag_type=TagType.SYSTEM
    )
    db_session.add(system_tag)
    db_session.commit()
    
    response = client.delete(f"/api/tags/{system_tag.id}")
    assert response.status_code == 403
    assert "system tags" in response.json()["detail"].lower()

def test_get_tag_downloads(client, sample_tag, sample_download):
    """Test getting downloads for a tag"""
    # Add download to tag
    sample_download.tags.append(sample_tag)
    db_session.commit()
    
    response = client.get(f"/api/tags/{sample_tag.id}/downloads")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0] == sample_download.id

def test_auto_assign_tag(client, sample_tag, db_session):
    """Test auto-assigning tag based on pattern"""
    # Set auto-assign pattern
    sample_tag.auto_assign_pattern = "test.*download"
    db_session.commit()
    
    # Create test downloads
    downloads = [
        Download(name="test_download_1", download_type=DownloadType.TORRENT),
        Download(name="test_download_2", download_type=DownloadType.TORRENT),
        Download(name="other_download", download_type=DownloadType.TORRENT)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    response = client.post(f"/api/tags/{sample_tag.id}/auto-assign")
    assert response.status_code == 200
    data = response.json()
    assert data["matched_count"] == 2

def test_batch_update_tags(client, sample_tag, db_session):
    """Test batch updating tags for multiple downloads"""
    # Create test downloads
    downloads = [
        Download(name="download_1", download_type=DownloadType.TORRENT),
        Download(name="download_2", download_type=DownloadType.TORRENT)
    ]
    for d in downloads:
        db_session.add(d)
    db_session.commit()
    
    download_ids = [d.id for d in downloads]
    
    response = client.post(
        "/api/tags/batch-update",
        json={
            "download_ids": download_ids,
            "add_tags": [sample_tag.id]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["affected_downloads"] == 2

def test_merge_tags(client, sample_tag, db_session):
    """Test merging two tags"""
    # Create second tag
    second_tag = Tag(
        name="Second Tag",
        color="#00ff00",
        tag_type=TagType.CUSTOM
    )
    db_session.add(second_tag)
    db_session.commit()
    
    # Create download with second tag
    download = Download(
        name="test_download",
        download_type=DownloadType.TORRENT,
        tags=[second_tag]
    )
    db_session.add(download)
    db_session.commit()
    
    response = client.post(f"/api/tags/merge/{second_tag.id}/{sample_tag.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["affected_downloads"] == 1
    
    # Verify second tag is deleted and download has first tag
    response = client.get(f"/api/tags/{second_tag.id}")
    assert response.status_code == 404
    
    response = client.get(f"/api/tags/{sample_tag.id}/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0] == download.id
