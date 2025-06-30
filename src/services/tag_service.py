import re
from typing import List, Optional
from datetime import datetime
from ..models.download import Tag, Download
from ..models.tables import TagTable, download_tags
from ..database import SessionLocal
from ..config import settings
import os
from sqlalchemy.orm import joinedload

class TagService:
    def __init__(self):
        self._initialize_default_tags()

    def _initialize_default_tags(self):
        """Initialize some default tags for common use cases if they don't exist."""
        db = SessionLocal()
        try:
            # Check if any tags exist
            existing_count = db.query(TagTable).count()
            if existing_count > 0:
                return  # Tags already exist, don't recreate
            
            default_tags = [
                {
                    'name': 'Movies',
                    'color': '#ef4444',
                    'destination_folder': '/downloads/movies',
                    'auto_assign_pattern': r'.*\.(avi|mkv|mp4|mov)$',
                    'description': 'Movie downloads'
                },
                {
                    'name': 'TV Shows',
                    'color': '#10b981', 
                    'destination_folder': '/downloads/tv',
                    'auto_assign_pattern': r'.*[Ss]\d+[Ee]\d+.*',
                    'description': 'TV show episodes'
                },
                {
                    'name': 'Music',
                    'color': '#8b5cf6',
                    'destination_folder': '/downloads/music',
                    'auto_assign_pattern': r'.*\.(mp3|flac|wav|m4a)$',
                    'description': 'Music downloads'
                },
                {
                    'name': 'Books',
                    'color': '#f59e0b',
                    'destination_folder': '/downloads/books',
                    'auto_assign_pattern': r'.*\.(pdf|epub|mobi)$',
                    'description': 'E-book downloads'
                },
                {
                    'name': 'Software',
                    'color': '#6b7280',
                    'destination_folder': '/downloads/software',
                    'auto_assign_pattern': r'.*\.(exe|dmg|pkg|deb|rpm)$',
                    'description': 'Software and applications'
                }
            ]
            
            for tag_data in default_tags:
                tag_table = TagTable(**tag_data)
                db.add(tag_table)
            
            db.commit()
        finally:
            db.close()

    def _tag_table_to_model(self, tag_table: TagTable) -> Tag:
        """Convert TagTable to Tag model."""
        return Tag(
            id=tag_table.id,
            name=tag_table.name,
            color=tag_table.color,
            destination_folder=tag_table.destination_folder,
            auto_assign_pattern=tag_table.auto_assign_pattern,
            description=tag_table.description,
            created_at=tag_table.created_at,
            updated_at=tag_table.updated_at
        )

    def create_tag(self, name: str, color: str = '#3b82f6', 
                   destination_folder: Optional[str] = None,
                   auto_assign_pattern: Optional[str] = None,
                   description: Optional[str] = None) -> Tag:
        """Create a new tag."""
        db = SessionLocal()
        try:
            tag_table = TagTable(
                name=name,
                color=color,
                destination_folder=destination_folder,
                auto_assign_pattern=auto_assign_pattern,
                description=description
            )
            db.add(tag_table)
            db.commit()
            db.refresh(tag_table)
            return self._tag_table_to_model(tag_table)
        finally:
            db.close()

    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """Get a tag by ID."""
        db = SessionLocal()
        try:
            tag_table = db.query(TagTable).filter(TagTable.id == tag_id).first()
            if tag_table:
                return self._tag_table_to_model(tag_table)
            return None
        finally:
            db.close()

    def get_all_tags(self) -> List[Tag]:
        """Get all tags."""
        db = SessionLocal()
        try:
            tag_tables = db.query(TagTable).all()
            return [self._tag_table_to_model(tag_table) for tag_table in tag_tables]
        finally:
            db.close()

    def update_tag(self, tag_id: int, **kwargs) -> Optional[Tag]:
        """Update a tag."""
        db = SessionLocal()
        try:
            tag_table = db.query(TagTable).filter(TagTable.id == tag_id).first()
            if not tag_table:
                return None
            
            for key, value in kwargs.items():
                if hasattr(tag_table, key):
                    setattr(tag_table, key, value)
            
            tag_table.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(tag_table)
            return self._tag_table_to_model(tag_table)
        finally:
            db.close()

    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag."""
        db = SessionLocal()
        try:
            tag_table = db.query(TagTable).filter(TagTable.id == tag_id).first()
            if tag_table:
                # Remove all associations first
                db.execute(download_tags.delete().where(download_tags.c.tag_id == tag_id))
                db.delete(tag_table)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def auto_assign_tags(self, download: Download) -> List[Tag]:
        """Automatically assign tags to a download based on patterns."""
        assigned_tags = []
        
        db = SessionLocal()
        try:
            tag_tables = db.query(TagTable).filter(TagTable.auto_assign_pattern.isnot(None)).all()
            
            for tag_table in tag_tables:
                if tag_table.auto_assign_pattern:
                    try:
                        if re.search(tag_table.auto_assign_pattern, download.name, re.IGNORECASE):
                            assigned_tags.append(self._tag_table_to_model(tag_table))
                    except re.error:
                        # Invalid regex pattern, skip
                        continue
        finally:
            db.close()
        
        return assigned_tags

    def get_destination_folder(self, tags: List[Tag], default_path: str) -> str:
        """Get the destination folder based on tags priority."""
        # Use the first tag with a destination folder
        for tag in tags:
            if tag.destination_folder:
                return tag.destination_folder
        return default_path

    def ensure_folder_exists(self, folder_path: str) -> bool:
        """Ensure the destination folder exists."""
        try:
            os.makedirs(folder_path, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False

    def get_tags_by_names(self, tag_names: List[str]) -> List[Tag]:
        """Get tags by their names."""
        db = SessionLocal()
        try:
            tag_tables = db.query(TagTable).filter(TagTable.name.in_(tag_names)).all()
            return [self._tag_table_to_model(tag_table) for tag_table in tag_tables]
        finally:
            db.close()

    def add_tag_to_download(self, download: Download, tag_id: int) -> bool:
        """Add a tag to a download."""
        db = SessionLocal()
        try:
            # Check if association already exists
            existing = db.execute(
                download_tags.select().where(
                    (download_tags.c.download_id == download.id) & 
                    (download_tags.c.tag_id == tag_id)
                )
            ).first()
            
            if existing:
                return False  # Already associated
            
            # Create association
            db.execute(
                download_tags.insert().values(
                    download_id=download.id,
                    tag_id=tag_id
                )
            )
            
            # Get tag for destination folder update
            tag_table = db.query(TagTable).filter(TagTable.id == tag_id).first()
            if tag_table and tag_table.destination_folder:
                # Update download path in downloads table  
                from ..models.tables import DownloadTable
                download_table = db.query(DownloadTable).filter(DownloadTable.id == download.id).first()
                if download_table:
                    download_table.download_path = tag_table.destination_folder
                    download_table.updated_at = datetime.utcnow()
                    self.ensure_folder_exists(tag_table.destination_folder)
            
            db.commit()
            return True
        finally:
            db.close()

    def remove_tag_from_download(self, download: Download, tag_id: int) -> bool:
        """Remove a tag from a download."""
        db = SessionLocal()
        try:
            result = db.execute(
                download_tags.delete().where(
                    (download_tags.c.download_id == download.id) & 
                    (download_tags.c.tag_id == tag_id)
                )
            )
            
            if result.rowcount > 0:
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_tags_for_download(self, download_id: int) -> List[Tag]:
        """Get all tags associated with a download."""
        db = SessionLocal()
        try:
            tag_tables = db.query(TagTable).join(
                download_tags, TagTable.id == download_tags.c.tag_id
            ).filter(download_tags.c.download_id == download_id).all()
            
            return [self._tag_table_to_model(tag_table) for tag_table in tag_tables]
        finally:
            db.close()
