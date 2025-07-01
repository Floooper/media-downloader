from enum import Enum

class DownloadType(str, Enum):
    """Type of download"""
    TORRENT = "torrent"
    NZB = "nzb"
    DIRECT = "direct"

class DownloadStatus(str, Enum):
    """Status of a download"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TagType(str, Enum):
    """Type of tag"""
    CATEGORY = "category"
    CUSTOM = "custom"
    SYSTEM = "system"
