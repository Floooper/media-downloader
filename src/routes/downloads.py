from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from ..services.nzb_service import NZBService
from ..settings import settings
from ..database import get_db, Download, DownloadStatus
from typing import List
import os
from datetime import datetime

router = APIRouter()

# Initialize NZB service with config
nzb_service = NZBService({
    "host": settings.USENET_SERVER,
    "port": settings.USENET_PORT,
    "ssl": settings.USENET_SSL,
    "username": settings.USENET_USERNAME,
    "password": settings.USENET_PASSWORD,
    "max_connections": settings.USENET_CONNECTIONS,
    "retention_days": settings.USENET_RETENTION
})

@router.get("/downloads/")
async def list_downloads(db: Session = Depends(get_db)):
    return db.query(Download).all()

@router.post("/downloads/nzb-file")
async def upload_nzb(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        nzb_content = content.decode()
        
        # Get paths from config
        download_path = settings.DEFAULT_DOWNLOAD_PATH
        temp_path = settings.TEMP_DOWNLOAD_PATH
        
        # Ensure directories exist
        os.makedirs(download_path, exist_ok=True)
        os.makedirs(temp_path, exist_ok=True)
        
        # Create download record
        download = Download(
            filename=file.filename,
            status=DownloadStatus.PENDING,
            download_path=os.path.join(download_path, file.filename)
        )
        db.add(download)
        db.commit()
        db.refresh(download)
        
        # Process NZB file
        result = await nzb_service.add_nzb_download(
            nzb_content=nzb_content,
            filename=file.filename,
            download_path=download_path,
            download_id=download.id
        )
        
        if result:
            download.status = DownloadStatus.DOWNLOADING
        else:
            download.status = DownloadStatus.FAILED
        
        db.commit()
        
        return {"status": "success" if result else "failed", "download_id": download.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/downloads/{download_id}")
async def get_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    return download

@router.post("/downloads/{download_id}/pause")
async def pause_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download.status = DownloadStatus.PAUSED
    db.commit()
    return {"status": "success"}

@router.post("/downloads/{download_id}/resume")
async def resume_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    download.status = DownloadStatus.DOWNLOADING
    db.commit()
    return {"status": "success"}

@router.delete("/downloads/{download_id}")
async def delete_download(download_id: int, db: Session = Depends(get_db)):
    download = db.query(Download).filter(Download.id == download_id).first()
    if not download:
        raise HTTPException(status_code=404, detail="Download not found")
    
    # TODO: Cancel active download if needed
    
    db.delete(download)
    db.commit()
    return {"status": "success"}
