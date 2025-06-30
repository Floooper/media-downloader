from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class DownloadType(str, Enum):
    TORRENT = "torrent"
    NZB = "nzb"

class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

# Association table for downloads and tags
download_tags = Table(
    'download_tags',
    Base.metadata,
    Column('download_id', Integer, ForeignKey('downloads.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class DownloadTable(Base):
    __tablename__ = 'downloads'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)  # Store magnet links, torrent URLs, etc.
    status = Column(String(50), nullable=False, default='queued')
    progress = Column(Float, default=0.0)
    download_type = Column(String(50), nullable=False)
    download_path = Column(Text, nullable=False)
    speed = Column(Float, default=0.0)
    eta = Column(String(100), default='')
    error_message = Column(Text, nullable=True)  # Store error details for failed downloads
    queued_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # NZB-specific fields
    nzb_content = Column(Text, nullable=True)  # Store NZB file content
    filename = Column(String(255), nullable=True)  # Original filename
    file_path = Column(Text, nullable=True)  # Path to downloaded file
    
    # Relationships
    tags = relationship("TagTable", secondary=download_tags, back_populates="downloads")

class TagTable(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default='#3b82f6')  # Hex color
    destination_folder = Column(Text, nullable=True)
    auto_assign_pattern = Column(Text, nullable=True)  # Regex pattern
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    downloads = relationship("DownloadTable", secondary=download_tags, back_populates="tags")
