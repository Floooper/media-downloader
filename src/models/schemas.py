from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from .enums import DownloadStatus, DownloadType, TagType

class TagBase(BaseModel):
    """Base Tag schema"""
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default='#3b82f6', pattern=r'^#[0-9a-fA-F]{6}$')
    tag_type: TagType = Field(default=TagType.CUSTOM)
    destination_folder: Optional[str] = Field(None, max_length=1024)
    auto_assign_pattern: Optional[str] = None
    description: Optional[str] = None

class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass

class TagUpdate(TagBase):
    """Schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    tag_type: Optional[TagType] = None

class Tag(TagBase):
    """Complete Tag schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DownloadBase(BaseModel):
    """Base Download schema"""
    name: str = Field(..., min_length=1, max_length=255)
    url: Optional[str] = None
    download_type: DownloadType
    download_path: str = Field(..., max_length=1024)
    file_size: Optional[int] = Field(None, ge=0)

class DownloadCreate(DownloadBase):
    """Schema for creating a new download"""
    tag_ids: Optional[List[int]] = Field(default=[])

    @validator('tag_ids')
    def validate_tag_ids(cls, v):
        if not all(isinstance(id, int) and id > 0 for id in v):
            raise ValueError("All tag IDs must be positive integers")
        return v

class DownloadUpdate(BaseModel):
    """Schema for updating a download"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[DownloadStatus] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    download_path: Optional[str] = Field(None, max_length=1024)
    speed: Optional[float] = Field(None, ge=0)
    eta: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None
    tag_ids: Optional[List[int]] = None

    @validator('tag_ids')
    def validate_tag_ids(cls, v):
        if v is not None and not all(isinstance(id, int) and id > 0 for id in v):
            raise ValueError("All tag IDs must be positive integers")
        return v

class Download(DownloadBase):
    """Complete Download schema"""
    id: int
    status: DownloadStatus
    progress: float = Field(0.0, ge=0, le=100)
    speed: float = Field(0.0, ge=0)
    eta: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None
    tags: List[Tag] = []
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DownloadProgress(BaseModel):
    """Download progress update schema"""
    id: int
    progress: float = Field(..., ge=0, le=100)
    speed: float = Field(..., ge=0)
    eta: Optional[str] = Field(None, max_length=50)
    status: DownloadStatus

class DownloadFilter(BaseModel):
    """Download filter schema"""
    status: Optional[List[DownloadStatus]] = None
    download_type: Optional[List[DownloadType]] = None
    tag_ids: Optional[List[int]] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class DownloadSort(BaseModel):
    """Download sort schema"""
    field: str = Field(..., regex='^(name|status|progress|created_at|updated_at)$')
    direction: str = Field(..., regex='^(asc|desc)$')
