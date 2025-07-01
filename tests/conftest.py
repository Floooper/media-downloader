import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from ..src.database import Base, get_db
from ..src.models.tables import Download, Tag
from ..src.models.enums import DownloadStatus, DownloadType, TagType
from ..src.api import create_app
from ..src.config import settings
from datetime import datetime

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with a clean database."""
    app = create_app()
    
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_download(db_session):
    """Create a sample download for testing."""
    download = Download(
        name="Test Download",
        url="magnet:?xt=test",
        status=DownloadStatus.QUEUED,
        progress=0.0,
        download_type=DownloadType.TORRENT,
        download_path="/downloads/test",
        created_at=datetime.utcnow()
    )
    db_session.add(download)
    db_session.commit()
    return download

@pytest.fixture
def sample_tag(db_session):
    """Create a sample tag for testing."""
    tag = Tag(
        name="Test Tag",
        color="#ff0000",
        tag_type=TagType.CUSTOM,
        created_at=datetime.utcnow()
    )
    db_session.add(tag)
    db_session.commit()
    return tag

@pytest.fixture
def mock_services(monkeypatch):
    """Mock service dependencies for testing."""
    class MockDownloadService:
        async def get_download(self, download_id):
            return None
        
        async def add_nzb(self, nzb_content, download_path, filename):
            return None
        
        async def add_magnet_download(self, magnet_link, download_path):
            return None
    
    class MockQueueService:
        async def get_queue(self, status=None):
            return []
        
        async def get_stats(self):
            return {
                "total_items": 0,
                "active_downloads": 0,
                "queued_downloads": 0,
                "completed_downloads": 0,
                "failed_downloads": 0,
                "total_progress": 0,
                "average_speed": 0
            }
    
    class MockSystemService:
        async def get_status(self):
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            }
    
    class MockServices:
        def get_download_service(self):
            return MockDownloadService()
        
        def get_queue_manager(self):
            return MockQueueService()
        
        def get_system_service(self):
            return MockSystemService()
    
    monkeypatch.setattr("src.services_manager.services", MockServices())
