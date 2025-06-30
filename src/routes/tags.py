from fastapi import APIRouter

router = APIRouter()

@router.get("/tags/")
async def list_tags():
    return []
