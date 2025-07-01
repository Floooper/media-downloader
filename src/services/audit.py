import logging
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
from ..models.user import AuditLog
from datetime import datetime
import json

logger = logging.getLogger(__name__)

async def create_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """Create an audit log entry"""
    try:
        # Get request information if available
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent")
        
        # Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        db.rollback()
        # Don't raise exception - audit logging should not break main functionality
        return None

class AuditLogger:
    """Audit logger class for use as a context manager"""
    def __init__(
        self,
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        request: Optional[Request] = None
    ):
        self.db = db
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.request = request
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None

    async def __aenter__(self):
        """Enter the context manager"""
        self.start_time = datetime.utcnow()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager"""
        self.end_time = datetime.utcnow()
        self.success = exc_type is None
        self.error = str(exc_val) if exc_val else None
        
        # Create audit log
        details = {
            "duration": (self.end_time - self.start_time).total_seconds(),
            "success": self.success
        }
        
        if self.error:
            details["error"] = self.error
        
        await create_audit_log(
            db=self.db,
            user_id=self.user_id,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            details=details,
            request=self.request
        )
        
        # Don't suppress exceptions
        return False

async def get_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    success_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """Get audit logs with filtering"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if success_only:
        query = query.filter(
            AuditLog.details.like('%"success": true%')
        )
    
    return query.order_by(
        AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()

async def get_audit_summary(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get summary of audit logs"""
    query = db.query(AuditLog)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Get total counts
    total_logs = query.count()
    success_logs = query.filter(
        AuditLog.details.like('%"success": true%')
    ).count()
    error_logs = query.filter(
        AuditLog.details.like('%"error"%')
    ).count()
    
    # Get counts by action
    action_counts = {}
    for action, count in db.query(
        AuditLog.action,
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.action).all():
        action_counts[action] = count
    
    # Get counts by resource type
    resource_counts = {}
    for resource_type, count in db.query(
        AuditLog.resource_type,
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.resource_type).all():
        resource_counts[resource_type] = count
    
    # Get most active users
    user_counts = {}
    for user_id, count in db.query(
        AuditLog.user_id,
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.user_id).all():
        user_counts[str(user_id)] = count
    
    return {
        "total_logs": total_logs,
        "success_logs": success_logs,
        "error_logs": error_logs,
        "success_rate": (success_logs / total_logs * 100) if total_logs > 0 else 0,
        "action_counts": action_counts,
        "resource_counts": resource_counts,
        "user_counts": user_counts
    }

async def cleanup_audit_logs(
    db: Session,
    before_date: datetime,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Clean up old audit logs"""
    query = db.query(AuditLog).filter(AuditLog.created_at < before_date)
    count = query.count()
    
    if not dry_run:
        try:
            query.delete()
            db.commit()
        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {e}")
            db.rollback()
            raise
    
    return {
        "logs_to_delete": count,
        "dry_run": dry_run,
        "before_date": before_date.isoformat()
    }
