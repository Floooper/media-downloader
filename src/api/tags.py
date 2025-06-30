from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict
import logging
import traceback
from ..services_manager import services
from ..models.download import Tag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tags", tags=["tags"])
tag_service = services.get_tag_service()

class TagCreate(BaseModel):
    name: str
    color: str = '#3b82f6'
    destination_folder: Optional[str] = None
    auto_assign_pattern: Optional[str] = None
    description: Optional[str] = None

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    destination_folder: Optional[str] = None
    auto_assign_pattern: Optional[str] = None
    description: Optional[str] = None

@router.get("/")
async def get_tags() -> List[Tag]:
    """Get all tags."""
    return tag_service.get_all_tags()

@router.get("/{tag_id}")
async def get_tag(tag_id: int) -> Tag:
    """Get a specific tag."""
    tag = tag_service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.post("/")
async def create_tag(tag: TagCreate) -> Tag:
    """Create a new tag."""
    try:
        return tag_service.create_tag(
            name=tag.name,
            color=tag.color,
            destination_folder=tag.destination_folder,
            auto_assign_pattern=tag.auto_assign_pattern,
            description=tag.description
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{tag_id}")
async def update_tag(tag_id: int, tag_update: TagUpdate) -> Tag:
    """Update a tag."""
    # Filter out None values
    update_data = {k: v for k, v in tag_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    updated_tag = tag_service.update_tag(tag_id, **update_data)
    if not updated_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return updated_tag

@router.delete("/{tag_id}")
async def delete_tag(tag_id: int) -> Dict:
    """Delete a tag."""
    success = tag_service.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return {"status": "success", "message": "Tag deleted"}

@router.post("/validate-pattern")
async def validate_pattern(pattern: str) -> Dict:
    """Validate a regex pattern."""
    import re
    try:
        re.compile(pattern)
        return {"valid": True, "message": "Pattern is valid"}
    except re.error as e:
        return {"valid": False, "message": f"Invalid pattern: {str(e)}"}

@router.get("/test-pattern/{tag_id}")
async def test_pattern(tag_id: int, test_string: str) -> Dict:
    """Test a tag's auto-assign pattern against a string."""
    tag = tag_service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if not tag.auto_assign_pattern:
        return {"matches": False, "message": "Tag has no auto-assign pattern"}
    
    import re
    try:
        matches = bool(re.search(tag.auto_assign_pattern, test_string, re.IGNORECASE))
        return {"matches": matches, "message": f"Pattern {'matches' if matches else 'does not match'}"}
    except re.error as e:
        return {"matches": False, "message": f"Pattern error: {str(e)}"}

