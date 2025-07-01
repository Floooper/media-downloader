from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Enum, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from .enums import DownloadStatus, DownloadType, TagType

# Association table for download tags
download_tags = Table(
    'download_tags',
    Base.metadata,
    Column('download_id', Integer, ForeignKey('downloads.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_download_tags_download_id', 'download_id'),
    Index('idx_download_tags_tag_id', 'tag_id')
)

class Download(Base):
    """Download table for tracking downloads"""
    __tablename__ = 'downloads'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(Text, nullable=True)
    status = Column(Enum(DownloadStatus), nullable=False, default=DownloadStatus.QUEUED, index=True)
    progress = Column(Float, nullable=False, default=0.0)
    download_type = Column(Enum(DownloadType), nullable=False, index=True)
    download_path = Column(String(1024), nullable=False)
    speed = Column(Float, nullable=False, default=0.0)  # bytes/sec
    eta = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Timestamps
    queued_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = relationship('Tag', secondary=download_tags, back_populates='downloads')
    
    __table_args__ = (
        Index('idx_downloads_status_type', 'status', 'download_type'),
        Index('idx_downloads_created_at', 'created_at'),
        {'extend_existing': True}
    )

class Tag(Base):
    """Tags for categorizing downloads"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=False, default='#3b82f6')  # Hex color code
    tag_type = Column(Enum(TagType), nullable=False, default=TagType.CUSTOM)
    destination_folder = Column(String(1024), nullable=True)
    auto_assign_pattern = Column(Text, nullable=True)  # Regex pattern
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    downloads = relationship('Download', secondary=download_tags, back_populates='tags')
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_tags_name'),
        Index('idx_tags_type', 'tag_type'),
        {'extend_existing': True}
    )

# Create indexes for foreign keys
Index('idx_download_tags_composite', download_tags.c.download_id, download_tags.c.tag_id)
