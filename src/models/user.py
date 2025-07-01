from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, constr
from ..database import Base

# Association table for user roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'))
)

class User(Base):
    """User database model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    api_keys = relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='user')

class Role(Base):
    """Role database model"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(String(500))  # JSON string of permissions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')

class APIKey(Base):
    """API key database model"""
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    scopes = Column(String(200))  # JSON string of scopes
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='api_keys')

class AuditLog(Base):
    """Audit log database model"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(String(500))  # JSON string of details
    ip_address = Column(String(45))  # IPv6-compatible
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='audit_logs')

# Pydantic models for API
class UserBase(BaseModel):
    """Base user schema"""
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema"""
    password: constr(min_length=8)

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[constr(min_length=8)] = None

class UserInDB(UserBase):
    """User database schema"""
    id: int
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    roles: List[str] = []

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    """Base role schema"""
    name: constr(min_length=1, max_length=50)
    description: Optional[str] = None
    permissions: List[str] = []

class RoleCreate(RoleBase):
    """Role creation schema"""
    pass

class RoleUpdate(BaseModel):
    """Role update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleInDB(RoleBase):
    """Role database schema"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyBase(BaseModel):
    """Base API key schema"""
    name: constr(min_length=1, max_length=100)
    scopes: List[str] = []
    expires_at: Optional[datetime] = None

class APIKeyCreate(APIKeyBase):
    """API key creation schema"""
    pass

class APIKeyInDB(APIKeyBase):
    """API key database schema"""
    id: int
    key: str
    user_id: int
    last_used: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    """Audit log creation schema"""
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogInDB(BaseModel):
    """Audit log database schema"""
    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
