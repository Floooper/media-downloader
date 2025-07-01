import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models.user import (
    Role, User, RoleCreate, RoleUpdate, RoleInDB, UserInDB
)
from ..auth import require_admin
from ..services.audit import create_audit_log
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[RoleInDB])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List roles with filtering and pagination"""
    query = db.query(Role)
    
    if search:
        query = query.filter(
            (Role.name.ilike(f"%{search}%")) |
            (Role.description.ilike(f"%{search}%"))
        )
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=RoleInDB)
async def create_role(
    role_create: RoleCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new role"""
    try:
        db_role = Role(
            name=role_create.name,
            description=role_create.description,
            permissions=json.dumps(role_create.permissions)
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="CREATE",
            resource_type="ROLE",
            resource_id=db_role.id,
            request=request
        )
        
        return db_role
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role")

@router.get("/{role_id}", response_model=RoleInDB)
async def get_role(
    role_id: int = Path(..., ge=1),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get role by ID"""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=RoleInDB)
async def update_role(
    role_update: RoleUpdate,
    role_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a role"""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Update role fields
        update_data = role_update.dict(exclude_unset=True)
        if "permissions" in update_data:
            update_data["permissions"] = json.dumps(update_data["permissions"])
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        db.commit()
        db.refresh(role)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            resource_type="ROLE",
            resource_id=role_id,
            details={"fields_updated": list(update_data.keys())},
            request=request
        )
        
        return role
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role")

@router.delete("/{role_id}")
async def delete_role(
    role_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a role"""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Check if role is in use
        if role.users:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete role that is assigned to users"
            )
        
        # Audit log before deletion
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="DELETE",
            resource_type="ROLE",
            resource_id=role_id,
            request=request
        )
        
        db.delete(role)
        db.commit()
        return {"message": "Role deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete role")

@router.get("/{role_id}/users", response_model=List[UserInDB])
async def get_role_users(
    role_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get users assigned to a role"""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role.users[skip:skip + limit]

@router.post("/{role_id}/clone", response_model=RoleInDB)
async def clone_role(
    role_id: int = Path(..., ge=1),
    name: str = Query(..., min_length=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Clone a role with a new name"""
    source_role = db.query(Role).get(role_id)
    if not source_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Create new role with same permissions
        new_role = Role(
            name=name,
            description=f"Clone of {source_role.name}",
            permissions=source_role.permissions
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="CLONE",
            resource_type="ROLE",
            resource_id=role_id,
            details={"new_role_id": new_role.id},
            request=request
        )
        
        return new_role
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error cloning role: {e}")
        raise HTTPException(status_code=500, detail="Failed to clone role")

@router.post("/{role_id}/permissions")
async def update_role_permissions(
    permissions: List[str],
    role_id: int = Path(..., ge=1),
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update role permissions"""
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        role.permissions = json.dumps(permissions)
        db.commit()
        
        # Audit log
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE_PERMISSIONS",
            resource_type="ROLE",
            resource_id=role_id,
            details={"permissions": permissions},
            request=request
        )
        
        return {"message": "Permissions updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating permissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to update permissions")
