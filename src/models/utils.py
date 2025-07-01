import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from ..database import engine, get_db
from . import tables
from .enums import DownloadStatus, DownloadType, TagType

logger = logging.getLogger(__name__)

def get_table_info() -> Dict[str, Any]:
    """Get information about database tables"""
    inspector = inspect(engine)
    
    table_info = {}
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "default": str(column["default"]) if column["default"] else None,
            })
        
        indexes = []
        for index in inspector.get_indexes(table_name):
            indexes.append({
                "name": index["name"],
                "unique": index["unique"],
                "columns": index["column_names"],
            })
        
        table_info[table_name] = {
            "columns": columns,
            "indexes": indexes,
            "primary_key": inspector.get_pk_constraint(table_name),
            "foreign_keys": inspector.get_foreign_keys(table_name),
        }
    
    return table_info

def verify_database_integrity() -> Dict[str, Any]:
    """Verify database integrity and constraints"""
    with get_db() as db:
        results = {
            "orphaned_tags": _check_orphaned_tags(db),
            "invalid_downloads": _check_invalid_downloads(db),
            "duplicate_tags": _check_duplicate_tags(db),
            "integrity_errors": _check_referential_integrity(db),
        }
        return results

def _check_orphaned_tags(db: Session) -> List[Dict[str, Any]]:
    """Check for tags with no associated downloads"""
    orphaned = []
    tags = db.query(tables.Tag).all()
    for tag in tags:
        if len(tag.downloads) == 0:
            orphaned.append({
                "id": tag.id,
                "name": tag.name,
                "created_at": tag.created_at,
            })
    return orphaned

def _check_invalid_downloads(db: Session) -> List[Dict[str, Any]]:
    """Check for downloads with invalid states or data"""
    invalid = []
    downloads = db.query(tables.Download).all()
    for download in downloads:
        errors = []
        
        # Check for invalid progress
        if not (0 <= download.progress <= 100):
            errors.append("Invalid progress value")
            
        # Check for completed downloads without completed_at
        if download.status == DownloadStatus.COMPLETED and not download.completed_at:
            errors.append("Completed download without completed_at timestamp")
            
        # Check for downloads with invalid paths
        if not download.download_path or download.download_path.isspace():
            errors.append("Invalid download path")
            
        if errors:
            invalid.append({
                "id": download.id,
                "name": download.name,
                "errors": errors,
            })
    return invalid

def _check_duplicate_tags(db: Session) -> List[Dict[str, Any]]:
    """Check for duplicate tag names"""
    duplicates = []
    result = db.execute(
        text("""
        SELECT name, COUNT(*) as count
        FROM tags
        GROUP BY name
        HAVING COUNT(*) > 1
        """)
    )
    for row in result:
        duplicates.append({
            "name": row.name,
            "count": row.count,
        })
    return duplicates

def _check_referential_integrity(db: Session) -> List[Dict[str, Any]]:
    """Check for referential integrity issues"""
    errors = []
    
    # Check download_tags references
    result = db.execute(
        text("""
        SELECT dt.download_id, dt.tag_id
        FROM download_tags dt
        LEFT JOIN downloads d ON dt.download_id = d.id
        LEFT JOIN tags t ON dt.tag_id = t.id
        WHERE d.id IS NULL OR t.id IS NULL
        """)
    )
    for row in result:
        errors.append({
            "table": "download_tags",
            "download_id": row.download_id,
            "tag_id": row.tag_id,
            "error": "Broken reference",
        })
    
    return errors

def cleanup_database(dry_run: bool = True) -> Dict[str, Any]:
    """Clean up database issues"""
    with get_db() as db:
        changes = {
            "orphaned_tags_removed": 0,
            "invalid_downloads_fixed": 0,
            "duplicate_tags_merged": 0,
            "broken_references_removed": 0,
        }
        
        if not dry_run:
            # Remove orphaned tags
            orphaned = _check_orphaned_tags(db)
            for tag in orphaned:
                db.execute(text("DELETE FROM tags WHERE id = :id"), {"id": tag["id"]})
                changes["orphaned_tags_removed"] += 1
            
            # Fix invalid downloads
            invalid = _check_invalid_downloads(db)
            for download in invalid:
                db.execute(
                    text("""
                    UPDATE downloads
                    SET progress = LEAST(GREATEST(progress, 0), 100),
                        download_path = COALESCE(NULLIF(download_path, ''), './downloads')
                    WHERE id = :id
                    """),
                    {"id": download["id"]}
                )
                changes["invalid_downloads_fixed"] += 1
            
            # Merge duplicate tags
            duplicates = _check_duplicate_tags(db)
            for dup in duplicates:
                # Keep the oldest tag and merge others into it
                tags = db.execute(
                    text("SELECT id FROM tags WHERE name = :name ORDER BY created_at"),
                    {"name": dup["name"]}
                ).fetchall()
                
                if len(tags) > 1:
                    keep_id = tags[0].id
                    merge_ids = [t.id for t in tags[1:]]
                    
                    # Update references
                    for merge_id in merge_ids:
                        db.execute(
                            text("""
                            INSERT INTO download_tags (download_id, tag_id)
                            SELECT download_id, :keep_id
                            FROM download_tags
                            WHERE tag_id = :merge_id
                            ON CONFLICT DO NOTHING
                            """),
                            {"keep_id": keep_id, "merge_id": merge_id}
                        )
                        
                        # Delete merged tag
                        db.execute(text("DELETE FROM tags WHERE id = :id"), {"id": merge_id})
                        changes["duplicate_tags_merged"] += 1
            
            # Remove broken references
            db.execute(text("""
                DELETE FROM download_tags
                WHERE download_id NOT IN (SELECT id FROM downloads)
                OR tag_id NOT IN (SELECT id FROM tags)
            """))
            changes["broken_references_removed"] = db.execute(
                text("SELECT ROW_COUNT()")
            ).scalar()
            
            db.commit()
        
        return changes
