import pytest
from fastapi.testclient import TestClient
from ..src.models.user import Role, User
from datetime import datetime

@pytest.fixture
def test_role(db_session):
    """Create a test role"""
    role = Role(
        name="test_role",
        description="Test Role",
        permissions="[]"
    )
    db_session.add(role)
    db_session.commit()
    return role

def test_create_role(client, admin_token):
    """Test role creation"""
    response = client.post(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "new_role",
            "description": "New Role",
            "permissions": ["downloads.read", "downloads.write"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new_role"
    assert data["description"] == "New Role"

def test_create_duplicate_role(client, admin_token, test_role):
    """Test creating role with duplicate name"""
    response = client.post(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": test_role.name,
            "description": "Duplicate Role"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_roles(client, admin_token, test_role):
    """Test getting role list"""
    response = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(r["name"] == test_role.name for r in data)

def test_get_role(client, admin_token, test_role):
    """Test getting specific role"""
    response = client.get(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_role.name

def test_update_role(client, admin_token, test_role):
    """Test updating role"""
    response = client.put(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "description": "Updated Description",
            "permissions": ["new.permission"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated Description"

def test_delete_role(client, admin_token, test_role):
    """Test deleting role"""
    response = client.delete(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify role is deleted
    response = client.get(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_delete_role_with_users(client, admin_token, test_role, normal_user, db_session):
    """Test deleting role that has users"""
    # Assign role to user
    normal_user.roles.append(test_role)
    db_session.commit()
    
    response = client.delete(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "assigned to users" in response.json()["detail"]

def test_get_role_users(client, admin_token, test_role, normal_user, db_session):
    """Test getting users with role"""
    # Assign role to user
    normal_user.roles.append(test_role)
    db_session.commit()
    
    response = client.get(
        f"/api/roles/{test_role.id}/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == normal_user.id

def test_clone_role(client, admin_token, test_role):
    """Test cloning role"""
    response = client.post(
        f"/api/roles/{test_role.id}/clone",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"name": "cloned_role"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "cloned_role"
    assert "Clone of" in data["description"]

def test_update_role_permissions(client, admin_token, test_role):
    """Test updating role permissions"""
    permissions = ["downloads.read", "downloads.write", "queue.manage"]
    response = client.post(
        f"/api/roles/{test_role.id}/permissions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=permissions
    )
    assert response.status_code == 200
    
    # Verify permissions were updated
    response = client.get(
        f"/api/roles/{test_role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert sorted(data["permissions"]) == sorted(permissions)

def test_search_roles(client, admin_token, db_session):
    """Test searching roles"""
    # Create multiple roles
    roles = [
        Role(name="admin_role", description="Admin Role"),
        Role(name="user_role", description="User Role"),
        Role(name="manager_role", description="Manager Role")
    ]
    for role in roles:
        db_session.add(role)
    db_session.commit()
    
    # Search by name
    response = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"search": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "admin_role"
    
    # Search by description
    response = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"search": "Manager"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "manager_role"

def test_role_pagination(client, admin_token, db_session):
    """Test role pagination"""
    # Create multiple roles
    roles = [
        Role(name=f"role_{i}", description=f"Role {i}")
        for i in range(10)
    ]
    for role in roles:
        db_session.add(role)
    db_session.commit()
    
    # Test first page
    response = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"skip": 0, "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test second page
    response = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"skip": 5, "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Verify different results
    first_page = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"skip": 0, "limit": 5}
    ).json()
    second_page = client.get(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"skip": 5, "limit": 5}
    ).json()
    assert all(r1["id"] != r2["id"] for r1 in first_page for r2 in second_page)
