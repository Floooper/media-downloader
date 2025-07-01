import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from .config import settings

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = settings.DATABASE_URL
POOL_SIZE = settings.DATABASE_POOL_SIZE
MAX_OVERFLOW = settings.DATABASE_MAX_OVERFLOW
POOL_TIMEOUT = settings.DATABASE_POOL_TIMEOUT

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_pre_ping=True  # Enable connection health checks
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Create MetaData instance
metadata = MetaData()

# Create base class for declarative models
Base = declarative_base(metadata=metadata)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """Initialize database schema"""
    try:
        # Import all models to ensure they're registered
        from .models import tables  # noqa

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def check_db_connection() -> bool:
    """Check database connection health"""
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

def get_db_stats() -> dict:
    """Get database connection pool statistics"""
    return {
        "pool_size": engine.pool.size(),
        "checkedout_connections": engine.pool.checkedout(),
        "overflow_connections": engine.pool.overflow(),
        "checkedin_connections": engine.pool.checkedin(),
    }
