import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models.user import (
    User, Role, APIKey, AuditLog,
    UserCreate, UserUpdate, UserInDB,
    RoleCreate, RoleUpdate, RoleInDB,
    APIKeyCreate, APIKeyInDB,
    AuditLogInDB
)
from ..auth import (
    get_current_active_user,
    get_password_hash,
    create_access_token,
    require_admin
)
from ..services.audit import create_audit_log
from datetime import datetime, timedelta
import secrets
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserInDB)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.patch("/me", response_model=UserInDB)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        # Update user fields
        for field, value in user_update.dict(exclude_unset=True).items():
            if field == "password":
                value = get_password_hash(value)
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            resource_type="USER",
            resource_id=current_user.id,
            details={"fields_updated": list(user_update.dict(exclude_unset=True).keys())},
            request=request
        )
        
        return current_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.get("/", response_model=List[UserInDB])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List users with filtering and pagination"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=UserInDB)
async def create_user(
    user_create: UserCreate,
    request: Request,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=get_password_hash(user_create.password),
            is_active=user_create.is_active
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=db_user.id,
            action="CREATE",
            resource_type="USER",
            resource_id=db_user.id,
            request=request
        )
        
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int = Path(..., ge=1),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete own account")
        
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Audit log before deletion
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="DELETE",
            resource_type="USER",
            resource_id=user_id,
            request=request
        )
        
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@router.post("/{user_id}/roles/{role_id}")
async def assign_role(
    user_id: int = Path(..., ge=1),
    role_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign a role to a user"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        if role not in user.roles:
            user.roles.append(role)
            db.commit()
            
            # Audit log
            await create_audit_log(
                db=db,
                user_id=current_user.id,
                action="ASSIGN_ROLE",
                resource_type="USER",
                resource_id=user_id,
                details={"role_id": role_id},
                request=request
            )
            
        return {"message": "Role assigned successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning role: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign role")

@router.delete("/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: int = Path(..., ge=1),
    role_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove a role from a user"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        if role in user.roles:
            user.roles.remove(role)
            db.commit()
            
            # Audit log
            await create_audit_log(
                db=db,
                user_id=current_user.id,
                action="REMOVE_ROLE",
                resource_type="USER",
                resource_id=user_id,
                details={"role_id": role_id},
                request=request
            )
            
        return {"message": "Role removed successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing role: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove role")

@router.post("/{user_id}/api-keys", response_model=APIKeyInDB)
async def create_api_key(
    api_key_create: APIKeyCreate,
    user_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create an API key for a user"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Generate API key
        key = secrets.token_urlsafe(32)
        
        db_api_key = APIKey(
            key=key,
            name=api_key_create.name,
            user_id=user_id,
            scopes=json.dumps(api_key_create.scopes),
            expires_at=api_key_create.expires_at
        )
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="CREATE_API_KEY",
            resource_type="USER",
            resource_id=user_id,
            details={"api_key_id": db_api_key.id},
            request=request
        )
        
        return db_api_key
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@router.get("/{user_id}/api-keys", response_model=List[APIKeyInDB])
async def list_api_keys(
    user_id: int = Path(..., ge=1),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List API keys for a user"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.api_keys

@router.delete("/{user_id}/api-keys/{api_key_id}")
async def delete_api_key(
    user_id: int = Path(..., ge=1),
    api_key_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == user_id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    try:
        # Audit log before deletion
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="DELETE_API_KEY",
            resource_type="USER",
            resource_id=user_id,
            details={"api_key_id": api_key_id},
            request=request
        )
        
        db.delete(api_key)
        db.commit()
        return {"message": "API key deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")

@router.get("/{user_id}/audit-logs", response_model=List[AuditLogInDB])
async def get_user_audit_logs(
    user_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs for a user"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(
        AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()
