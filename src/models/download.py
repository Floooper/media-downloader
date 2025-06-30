from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class DownloadType(str, Enum):
    TORRENT = "torrent"
    NZB = "nzb"

class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class Tag(BaseModel):
    id: int
    name: str
    color: str = '#3b82f6'  # Default blue color
    destination_folder: Optional[str] = None
    auto_assign_pattern: Optional[str] = None  # Regex pattern for auto-assignment
    description: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Config:
        from_attributes = True

class Download(BaseModel):
    id: int
    name: str
    url: Optional[str] = None  # Magnet link, torrent URL, etc.
    status: DownloadStatus
    progress: float
    download_type: DownloadType
    download_path: str
    speed: float = 0.0  # MB/s
    eta: str = ''
    error_message: Optional[str] = None  # Store error details for failed downloads
    tags: List[Tag] = []
    queued_at: datetime = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Config:
        from_attributes = True
