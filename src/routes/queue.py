from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db, Download, DownloadStatus

router = APIRouter()

@router.post("/queue/{download_id}/pause")
async def pause_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download.status = DownloadStatus.PAUSED
    db.commit()
    return {"status": "success"}

@router.post("/queue/{download_id}/resume")
async def resume_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download.status = DownloadStatus.DOWNLOADING
    db.commit()
    return {"status": "success"}

@router.delete("/queue/{download_id}")
async def delete_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    db.delete(download)
    db.commit()
    return {"status": "success"}
