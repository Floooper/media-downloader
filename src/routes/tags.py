import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..database import get_db
from ..models.tables import Tag, Download
from ..models.schemas import TagCreate, TagUpdate, Tag as TagSchema
from ..models.enums import TagType
from ..services_manager import services

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[TagSchema])
async def list_tags(
    type: Optional[TagType] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all tags with optional filtering
    """
    try:
        query = db.query(Tag)
        
        if type:
            query = query.filter(Tag.tag_type == type)
        if search:
            query = query.filter(Tag.name.ilike(f"%{search}%"))
            
        return query.order_by(Tag.name).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in list_tags: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")

@router.post("/", response_model=TagSchema)
async def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tag
    """
    try:
        db_tag = Tag(**tag.model_dump())
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Tag name already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tag")

@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(
    tag_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get a specific tag by ID
    """
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/{tag_id}", response_model=TagSchema)
async def update_tag(
    tag_id: int = Path(..., ge=1),
    tag_update: TagUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Update a tag
    """
    try:
        db_tag = db.query(Tag).get(tag_id)
        if not db_tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Update fields
        for field, value in tag_update.model_dump(exclude_unset=True).items():
            setattr(db_tag, field, value)

        db.commit()
        db.refresh(db_tag)
        return db_tag
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Tag name already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tag")

@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Delete a tag
    """
    try:
        tag = db.query(Tag).get(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
            
        if tag.tag_type == TagType.SYSTEM:
            raise HTTPException(status_code=403, detail="Cannot delete system tags")
            
        db.delete(tag)
        db.commit()
        return {"message": "Tag deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tag")

@router.get("/{tag_id}/downloads", response_model=List[int])
async def get_tag_downloads(
    tag_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get all download IDs associated with a tag
    """
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return [download.id for download in tag.downloads]

@router.post("/{tag_id}/auto-assign")
async def auto_assign_tag(
    tag_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Auto-assign tag to matching downloads based on pattern
    """
    try:
        tag = db.query(Tag).get(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
            
        if not tag.auto_assign_pattern:
            raise HTTPException(status_code=400, detail="Tag has no auto-assign pattern")
            
        import re
        pattern = re.compile(tag.auto_assign_pattern)
        
        # Find matching downloads
        downloads = db.query(Download).all()
        matched_count = 0
        
        for download in downloads:
            if pattern.search(download.name):
                if tag not in download.tags:
                    download.tags.append(tag)
                    matched_count += 1
        
        db.commit()
        return {
            "message": f"Auto-assigned tag to {matched_count} downloads",
            "matched_count": matched_count
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error auto-assigning tag: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-assign tag")

@router.post("/batch-update")
async def batch_update_tags(
    download_ids: List[int],
    add_tags: Optional[List[int]] = None,
    remove_tags: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """
    Batch update tags for multiple downloads
    """
    try:
        if not add_tags and not remove_tags:
            raise HTTPException(status_code=400, detail="No tags specified to add or remove")
            
        # Validate downloads exist
        downloads = db.query(Download).filter(Download.id.in_(download_ids)).all()
        if len(downloads) != len(download_ids):
            raise HTTPException(status_code=400, detail="One or more invalid download IDs")
            
        # Process tag additions
        if add_tags:
            tags_to_add = db.query(Tag).filter(Tag.id.in_(add_tags)).all()
            if len(tags_to_add) != len(add_tags):
                raise HTTPException(status_code=400, detail="One or more invalid tag IDs to add")
                
            for download in downloads:
                for tag in tags_to_add:
                    if tag not in download.tags:
                        download.tags.append(tag)
                        
        # Process tag removals
        if remove_tags:
            tags_to_remove = db.query(Tag).filter(Tag.id.in_(remove_tags)).all()
            if len(tags_to_remove) != len(remove_tags):
                raise HTTPException(status_code=400, detail="One or more invalid tag IDs to remove")
                
            for download in downloads:
                for tag in tags_to_remove:
                    if tag in download.tags:
                        download.tags.remove(tag)
                        
        db.commit()
        return {
            "message": "Tags updated successfully",
            "affected_downloads": len(downloads)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch tag update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tags")

@router.post("/merge/{source_id}/{target_id}")
async def merge_tags(
    source_id: int = Path(..., ge=1),
    target_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Merge source tag into target tag
    """
    try:
        if source_id == target_id:
            raise HTTPException(status_code=400, detail="Cannot merge tag with itself")
            
        source_tag = db.query(Tag).get(source_id)
        target_tag = db.query(Tag).get(target_id)
        
        if not source_tag or not target_tag:
            raise HTTPException(status_code=404, detail="One or both tags not found")
            
        if source_tag.tag_type == TagType.SYSTEM:
            raise HTTPException(status_code=403, detail="Cannot merge system tags")
            
        # Move all downloads from source to target
        for download in source_tag.downloads:
            if target_tag not in download.tags:
                download.tags.append(target_tag)
                
        # Delete source tag
        db.delete(source_tag)
        db.commit()
        
        return {
            "message": "Tags merged successfully",
            "affected_downloads": len(source_tag.downloads)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error merging tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to merge tags")
