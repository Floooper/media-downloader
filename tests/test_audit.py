import pytest
from fastapi import Request
from datetime import datetime, timedelta
from ..src.models.user import AuditLog
from ..src.services.audit import (
    create_audit_log,
    AuditLogger,
    get_audit_logs,
    get_audit_summary,
    cleanup_audit_logs
)

class MockRequest:
    """Mock request class for testing"""
    class Client:
        host = "127.0.0.1"
    
    def __init__(self):
        self.client = self.Client()
        self.headers = {"user-agent": "test-agent"}

@pytest.fixture
def mock_request():
    """Create mock request"""
    return MockRequest()

@pytest.fixture
def sample_audit_logs(db_session):
    """Create sample audit logs"""
    logs = [
        AuditLog(
            user_id=1,
            action="CREATE",
            resource_type="USER",
            resource_id=1,
            details='{"success": true}',
            ip_address="127.0.0.1",
            user_agent="test-agent",
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        for i in range(5)
    ]
    for log in logs:
        db_session.add(log)
    db_session.commit()
    return logs

async def test_create_audit_log(db_session, mock_request):
    """Test creating audit log"""
    log = await create_audit_log(
        db=db_session,
        user_id=1,
        action="CREATE",
        resource_type="USER",
        resource_id=1,
        details={"test": "data"},
        request=mock_request
    )
    
    assert log is not None
    assert log.user_id == 1
    assert log.action == "CREATE"
    assert log.resource_type == "USER"
    assert log.ip_address == "127.0.0.1"
    assert log.user_agent == "test-agent"

async def test_audit_logger_context_manager(db_session, mock_request):
    """Test audit logger context manager"""
    async with AuditLogger(
        db=db_session,
        user_id=1,
        action="UPDATE",
        resource_type="USER",
        resource_id=1,
        request=mock_request
    ):
        # Simulate some work
        pass
    
    # Check that log was created
    log = db_session.query(AuditLog).first()
    assert log is not None
    assert log.action == "UPDATE"
    assert "success" in log.details
    assert "duration" in log.details

async def test_audit_logger_with_error(db_session, mock_request):
    """Test audit logger with error"""
    try:
        async with AuditLogger(
            db=db_session,
            user_id=1,
            action="DELETE",
            resource_type="USER",
            resource_id=1,
            request=mock_request
        ):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Check that error was logged
    log = db_session.query(AuditLog).first()
    assert log is not None
    assert log.action == "DELETE"
    assert "error" in log.details
    assert "Test error" in log.details

async def test_get_audit_logs_filtering(db_session, sample_audit_logs):
    """Test getting audit logs with filters"""
    # Test user filter
    logs = await get_audit_logs(db_session, user_id=1)
    assert len(logs) == 5
    
    # Test action filter
    logs = await get_audit_logs(db_session, action="CREATE")
    assert len(logs) == 5
    
    # Test resource type filter
    logs = await get_audit_logs(db_session, resource_type="USER")
    assert len(logs) == 5
    
    # Test date range filter
    logs = await get_audit_logs(
        db_session,
        start_date=datetime.utcnow() - timedelta(days=2),
        end_date=datetime.utcnow()
    )
    assert len(logs) == 3

async def test_get_audit_logs_pagination(db_session, sample_audit_logs):
    """Test audit log pagination"""
    # Test limit
    logs = await get_audit_logs(db_session, limit=2)
    assert len(logs) == 2
    
    # Test skip
    logs = await get_audit_logs(db_session, skip=2, limit=2)
    assert len(logs) == 2
    assert logs[0].created_at < sample_audit_logs[1].created_at

async def test_get_audit_summary(db_session, sample_audit_logs):
    """Test getting audit summary"""
    summary = await get_audit_summary(db_session)
    
    assert summary["total_logs"] == 5
    assert summary["success_logs"] == 5
    assert summary["error_logs"] == 0
    assert summary["success_rate"] == 100
    assert "action_counts" in summary
    assert "resource_counts" in summary
    assert "user_counts" in summary

async def test_cleanup_audit_logs(db_session, sample_audit_logs):
    """Test cleaning up old audit logs"""
    # Test dry run
    result = await cleanup_audit_logs(
        db_session,
        before_date=datetime.utcnow() - timedelta(days=3),
        dry_run=True
    )
    assert result["logs_to_delete"] == 2
    assert result["dry_run"] is True
    
    # Verify no logs were deleted
    assert db_session.query(AuditLog).count() == 5
    
    # Test actual cleanup
    result = await cleanup_audit_logs(
        db_session,
        before_date=datetime.utcnow() - timedelta(days=3),
        dry_run=False
    )
    assert result["logs_to_delete"] == 2
    
    # Verify logs were deleted
    assert db_session.query(AuditLog).count() == 3

async def test_audit_log_data_integrity(db_session, mock_request):
    """Test audit log data integrity"""
    # Create log with various data types
    details = {
        "string": "test",
        "number": 123,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "object": {"key": "value"}
    }
    
    log = await create_audit_log(
        db=db_session,
        user_id=1,
        action="TEST",
        resource_type="TEST",
        details=details,
        request=mock_request
    )
    
    # Verify data was stored correctly
    assert log is not None
    stored_details = log.details
    assert "string" in stored_details
    assert "number" in stored_details
    assert "boolean" in stored_details
    assert "array" in stored_details
    assert "object" in stored_details

async def test_audit_log_performance(db_session, mock_request):
    """Test audit log performance with bulk operations"""
    start_time = datetime.utcnow()
    
    # Create multiple logs
    logs = []
    for i in range(100):
        log = await create_audit_log(
            db=db_session,
            user_id=1,
            action=f"ACTION_{i}",
            resource_type="TEST",
            details={"index": i},
            request=mock_request
        )
        logs.append(log)
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    # Verify logs were created
    assert db_session.query(AuditLog).count() == 100
    
    # Performance should be reasonable
    assert duration < 5  # Should take less than 5 seconds
