from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from .config import settings
from .database import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    """User model"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: list[str] = []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "refresh": True})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user"""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user(db: Session, username: str) -> Optional[User]:
    """Get user from database"""
    # This should be implemented based on your user model
    # For now, returning a mock user
    if username == "admin":
        return User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            disabled=False,
            scopes=["admin"]
        )
    return None

async def check_permissions(
    required_scopes: list[str],
    user: User = Depends(get_current_active_user)
) -> bool:
    """Check if user has required permissions"""
    user_scopes = set(user.scopes)
    if "admin" in user_scopes:
        return True
    return all(scope in user_scopes for scope in required_scopes)

class PermissionChecker:
    """Permission checker dependency"""
    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes

    async def __call__(self, user: User = Depends(get_current_active_user)):
        if not await check_permissions(self.required_scopes, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user

# Common permission requirements
require_admin = PermissionChecker(["admin"])
require_download_manager = PermissionChecker(["downloads"])
require_queue_manager = PermissionChecker(["queue"])
require_tag_manager = PermissionChecker(["tags"])
require_system_manager = PermissionChecker(["system"])

async def refresh_token(refresh_token: str, db: Session) -> Token:
    """Refresh access token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not a refresh token"
            )
        
        user = get_user(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "scopes": user.scopes},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# API key authentication for media managers
class APIKeyAuth:
    """API key authentication for media managers"""
    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes

    async def __call__(
        self,
        api_key: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
        db: Session = Depends(get_db)
    ):
        # Validate API key (implement based on your storage method)
        if not is_valid_api_key(api_key, db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        return True

def is_valid_api_key(api_key: str, db: Session) -> bool:
    """Validate API key"""
    # This should be implemented based on your API key storage
    # For now, just checking against settings
    return api_key in [
        settings.SONARR_API_KEY,
        settings.RADARR_API_KEY,
        settings.READARR_API_KEY
    ]

# API key requirements for different media managers
require_sonarr_auth = APIKeyAuth(["sonarr"])
require_radarr_auth = APIKeyAuth(["radarr"])
require_readarr_auth = APIKeyAuth(["readarr"])
