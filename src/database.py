from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Enum as SQLEnum, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
from .config import config

# Get database URL from config
DATABASE_URL = config.get("database.url", "sqlite:///downloads.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create MetaData instance
metadata = MetaData()

# Create declarative base with our MetaData
Base = declarative_base(metadata=metadata)

# Define download status enum
class DownloadStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Define models
class Download(Base):
    __tablename__ = "downloads"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(SQLEnum(DownloadStatus), default=DownloadStatus.PENDING)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    file_size = Column(Integer, nullable=True)
    download_path = Column(String)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
