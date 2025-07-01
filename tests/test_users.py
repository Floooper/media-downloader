import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from ..src.models.user import User, Role, APIKey, UserCreate, RoleCreate
from ..src.auth import create_access_token, get_password_hash

@pytest.fixture
def admin_user(db_session):
    """Create an admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpass"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_token(admin_user):
    """Create admin access token"""
    return create_access_token(
        data={"sub": admin_user.username, "scopes": ["admin"]},
        expires_delta=timedelta(minutes=30)
    )

@pytest.fixture
def normal_user(db_session):
    """Create a normal user"""
    user = User(
        username="user",
        email="user@example.com",
        full_name="Normal User",
        hashed_password=get_password_hash("userpass"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def normal_token(normal_user):
    """Create normal user access token"""
    return create_access_token(
        data={"sub": normal_user.username},
        expires_delta=timedelta(minutes=30)
    )

def test_create_user(client, admin_token):
    """Test user creation"""
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "hashed_password" not in data

def test_create_duplicate_user(client, admin_token, normal_user):
    """Test creating user with duplicate username"""
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": normal_user.username,
            "email": "another@example.com",
            "password": "password"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_users(client, admin_token, normal_user):
    """Test getting user list"""
    response = client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(u["username"] == normal_user.username for u in data)

def test_get_user(client, admin_token, normal_user):
    """Test getting specific user"""
    response = client.get(
        f"/api/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == normal_user.username

def test_update_user(client, admin_token, normal_user):
    """Test updating user"""
    response = client.patch(
        f"/api/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Updated Name"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

def test_delete_user(client, admin_token, normal_user):
    """Test deleting user"""
    response = client.delete(
        f"/api/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify user is deleted
    response = client.get(
        f"/api/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_create_api_key(client, admin_token, normal_user):
    """Test creating API key"""
    response = client.post(
        f"/api/users/{normal_user.id}/api-keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Key",
            "scopes": ["downloads", "queue"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Key"
    assert "key" in data

def test_list_api_keys(client, admin_token, normal_user, db_session):
    """Test listing API keys"""
    # Create API key
    api_key = APIKey(
        key="testkey123",
        name="Test Key",
        user_id=normal_user.id,
        scopes="[]"
    )
    db_session.add(api_key)
    db_session.commit()
    
    response = client.get(
        f"/api/users/{normal_user.id}/api-keys",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Key"

def test_delete_api_key(client, admin_token, normal_user, db_session):
    """Test deleting API key"""
    # Create API key
    api_key = APIKey(
        key="testkey123",
        name="Test Key",
        user_id=normal_user.id,
        scopes="[]"
    )
    db_session.add(api_key)
    db_session.commit()
    
    response = client.delete(
        f"/api/users/{normal_user.id}/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify API key is deleted
    api_keys = db_session.query(APIKey).filter_by(user_id=normal_user.id).all()
    assert len(api_keys) == 0

def test_assign_role(client, admin_token, normal_user, db_session):
    """Test assigning role to user"""
    # Create role
    role = Role(name="test_role", permissions="[]")
    db_session.add(role)
    db_session.commit()
    
    response = client.post(
        f"/api/users/{normal_user.id}/roles/{role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify role is assigned
    user = db_session.query(User).get(normal_user.id)
    assert role in user.roles

def test_remove_role(client, admin_token, normal_user, db_session):
    """Test removing role from user"""
    # Create and assign role
    role = Role(name="test_role", permissions="[]")
    db_session.add(role)
    db_session.commit()
    normal_user.roles.append(role)
    db_session.commit()
    
    response = client.delete(
        f"/api/users/{normal_user.id}/roles/{role.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify role is removed
    user = db_session.query(User).get(normal_user.id)
    assert role not in user.roles

def test_get_audit_logs(client, admin_token, normal_user):
    """Test getting user audit logs"""
    response = client.get(
        f"/api/users/{normal_user.id}/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_unauthorized_access(client, normal_token):
    """Test unauthorized access to admin endpoints"""
    endpoints = [
        ("/api/users/", "GET"),
        ("/api/users/", "POST"),
        ("/api/users/1", "GET"),
        ("/api/users/1", "DELETE"),
        ("/api/users/1/roles/1", "POST"),
        ("/api/users/1/api-keys", "GET")
    ]
    
    for endpoint, method in endpoints:
        response = client.request(
            method,
            endpoint,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403

def test_user_update_self(client, normal_token, normal_user):
    """Test user updating own information"""
    response = client.patch(
        "/api/users/me",
        headers={"Authorization": f"Bearer {normal_token}"},
        json={
            "full_name": "Updated Self"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Self"

def test_get_current_user(client, normal_token, normal_user):
    """Test getting current user information"""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == normal_user.username
