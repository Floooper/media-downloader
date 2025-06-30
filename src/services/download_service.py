from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.tables import DownloadTable, DownloadStatus, DownloadType
from ..models.download import Download
from ..models.tables import DownloadTable
import json
import os

class DownloadService:
    def __init__(self):
        self.torrent_downloader = None
        self.nzb_downloader = None
        # Map download IDs to torrent IDs
        self.download_to_torrent_map: Dict[int, str] = {}
        self.mappings_file = "./data/torrent_mappings.json"
        self._load_torrent_mappings()

    def _load_torrent_mappings(self):
        """Load torrent mappings from persistent storage"""
        try:
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r') as f:
                    # Convert string keys back to integers
                    string_mappings = json.load(f)
                    self.download_to_torrent_map = {
                        int(k): v for k, v in string_mappings.items()
                    }
                print(f"Loaded {len(self.download_to_torrent_map)} torrent mappings")
        except Exception as e:
            print(f"Failed to load torrent mappings: {e}")
            self.download_to_torrent_map = {}

    def _save_torrent_mappings(self):
        """Save torrent mappings to persistent storage"""
        try:
            os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)
            # Convert integer keys to strings for JSON serialization
            string_mappings = {str(k): v for k, v in self.download_to_torrent_map.items()}
            with open(self.mappings_file, 'w') as f:
                json.dump(string_mappings, f)
        except Exception as e:
            print(f"Failed to save torrent mappings: {e}")

    def set_torrent_downloader(self, torrent_downloader):
        """Inject the torrent downloader service"""
        self.torrent_downloader = torrent_downloader
    
    def set_nzb_downloader(self, nzb_downloader):
        """Inject the NZB downloader service"""
        self.nzb_downloader = nzb_downloader

    def _get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()

    def _download_table_to_model(self, download_table: DownloadTable) -> Download:
        """Convert database table object to Pydantic model"""
        return Download(
            id=download_table.id,
            name=download_table.name,
            url=download_table.url,
            status=DownloadStatus(download_table.status),
            progress=download_table.progress,
            download_type=DownloadType(download_table.download_type),
            download_path=download_table.download_path,
            speed=download_table.speed,
            eta=download_table.eta,
            error_message=download_table.error_message,
            tags=[],  # TODO: Load tags from relationship
            queued_at=download_table.queued_at,
            created_at=download_table.created_at,
            updated_at=download_table.updated_at
        )

    def _model_to_download_table(self, download: Download) -> DownloadTable:
        """Convert Pydantic model to database table object"""
        return DownloadTable(
            id=download.id,
            name=download.name,
            url=download.url,
            status=download.status.value,
            progress=download.progress,
            download_type=download.download_type.value,
            download_path=download.download_path,
            speed=download.speed,
            eta=download.eta,
            queued_at=download.queued_at,
            created_at=download.created_at,
            updated_at=download.updated_at
        )

    async def add_torrent(self, magnet_link: str, download_path: str) -> Download:
        """Add a torrent download and start downloading"""
        db = self._get_db()
        try:
            # Create new download record
            download_table = DownloadTable(
                url=magnet_link,
                name=f"Torrent {datetime.now().strftime('%H:%M:%S')}",
                status=DownloadStatus.QUEUED,
                progress=0.0,
                download_type=DownloadType.TORRENT.value,
                download_path=download_path or "./downloads",
                speed=0.0,
                eta="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(download_table)
            db.commit()
            db.refresh(download_table)
            
            download = self._download_table_to_model(download_table)
            
            # Start actual torrent download if torrent downloader is available
            if self.torrent_downloader and magnet_link.startswith('magnet:'):
                try:
                    # Start the actual torrent download
                    torrent_id = await self.torrent_downloader.process_magnet_link(
                        magnet_link, download_path or "./downloads"
                    )
                    
                    # Map download ID to torrent ID and persist
                    self.download_to_torrent_map[download.id] = torrent_id
                    self._save_torrent_mappings()
                    
                    # Update download with torrent name and start downloading
                    torrent_info = self.torrent_downloader.get_torrent_status(torrent_id)
                    if torrent_info:
                        download_table.name = torrent_info.name
                        download_table.status = DownloadStatus.DOWNLOADING
                        db.commit()
                        
                        # Start the download
                        await self.torrent_downloader.start_download(torrent_id)
                        
                        download = self._download_table_to_model(download_table)
                        
                except Exception as e:
                    print(f"Failed to start torrent download: {e}")
                    # Keep the database entry but mark as failed
                    download_table.status = DownloadStatus.FAILED
                    download_table.error_message = str(e)
                    db.commit()
            
            return download
        finally:
            db.close()

    
    def _extract_nzb_name(self, nzb_content: str, filename: str = None) -> str:
        """Extract a meaningful name from NZB content or filename"""
        try:
            import xml.etree.ElementTree as ET
            
            # Try to parse NZB content to get the title
            root = ET.fromstring(nzb_content)
            
            # Look for title in meta tags
            for meta in root.findall('.//{http://www.newzbin.com/DTD/2003/nzb}meta'):
                if meta.get('type') == 'title':
                    title = meta.text
                    if title and title.strip():
                        return title.strip()
            
            # Look for subject in the first file
            for file_elem in root.findall('.//{http://www.newzbin.com/DTD/2003/nzb}file'):
                subject = file_elem.get('subject')
                if subject:
                    # Clean up the subject line to extract the actual name
                    # Remove common patterns like [01/15], (1/15), etc.
                    cleaned = re.sub(r'\[\d+/\d+\]|\(\d+/\d+\)', '', subject)
                    cleaned = re.sub(r'"([^"]+)"', r'\1', cleaned)  # Remove quotes
                    cleaned = cleaned.strip()
                    if cleaned:
                        return cleaned
                        
        except Exception:
            pass
        
        # Fall back to filename if provided
        if filename:
            # Remove .nzb extension and clean up
            name = filename.replace('.nzb', '').replace('.NZB', '')
            return name.strip() if name.strip() else f"NZB {datetime.now().strftime('%H:%M:%S')}"
        
        # Final fallback
        return f"NZB {datetime.now().strftime('%H:%M:%S')}"


    async def add_nzb(self, nzb_content, download_path: str, filename: str = None) -> Download:
        """Add an NZB download"""
        db = self._get_db()
        try:
            # Create new download record
            download_table = DownloadTable(
                url=f"nzb_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=self._extract_nzb_name(nzb_content, filename),
                status=DownloadStatus.QUEUED,
                progress=0.0,
                download_type=DownloadType.NZB.value,
                download_path=download_path or "./downloads",
                speed=0.0,
                eta="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(download_table)
            db.commit()
            db.refresh(download_table)
            
            download = self._download_table_to_model(download_table)
            
            # Start NZB download if downloader is available
            if self.nzb_downloader:
                try:
                    success = await self.nzb_downloader.add_nzb_download(
                        nzb_content, str(download_table.id), download_path
                    )
                    if success:
                        download_table.status = DownloadStatus.DOWNLOADING
                        db.commit()
                        download.status = DownloadStatus.DOWNLOADING
                        print(f"✅ Started NZB download: {download_table.id}")
                    else:
                        download_table.status = DownloadStatus.FAILED
                        download_table.error_message = "Failed to start NZB download"
                        db.commit()
                        download.status = DownloadStatus.FAILED
                        download.error_message = "Failed to start NZB download"
                except Exception as e:
                    print(f"❌ Error starting NZB download: {e}")
                    download_table.status = DownloadStatus.FAILED
                    download_table.error_message = str(e)
                    db.commit()
                    download.status = DownloadStatus.FAILED
                    download.error_message = str(e)
            
            return download
        finally:
            db.close()
            db.close()

    async def get_download(self, download_id: int) -> Optional[Download]:
        """Get a download by ID"""
        db = self._get_db()
        try:
            download_table = db.query(DownloadTable).filter(DownloadTable.id == download_id).first()
            if download_table:
                download = self._download_table_to_model(download_table)
                
                # Update with real-time torrent info if available
                if (self.torrent_downloader and 
                    download.download_type == DownloadType.TORRENT and
                    download_id in self.download_to_torrent_map):
                    try:
                        torrent_id = self.download_to_torrent_map[download_id]
                        torrent_info = self.torrent_downloader.get_torrent_status(torrent_id)
                        if torrent_info:
                            download.progress = torrent_info.progress
                            download.speed = torrent_info.download_rate
                            # Update status if different
                            if torrent_info.status == "downloading":
                                download.status = DownloadStatus.DOWNLOADING
                            elif torrent_info.status == "paused":
                                download.status = DownloadStatus.PAUSED
                            elif torrent_info.progress >= 100:
                                download.status = DownloadStatus.COMPLETED
                    except Exception:
                        pass  # Continue if we can't get torrent status
                
                return download
            return None
        finally:
            db.close()

    async def get_all_downloads(self) -> List[Download]:
        """Get all downloads"""
        db = self._get_db()
        try:
            download_tables = db.query(DownloadTable).all()
            downloads = [self._download_table_to_model(dt) for dt in download_tables]
            
            # Update progress from torrent downloader if available
            if self.torrent_downloader:
                for download in downloads:
                    if (download.download_type == DownloadType.TORRENT and 
                        download.id in self.download_to_torrent_map):
                        try:
                            torrent_id = self.download_to_torrent_map[download.id]
                            torrent_info = self.torrent_downloader.get_torrent_status(torrent_id)
                            if torrent_info:
                                download.progress = torrent_info.progress
                                download.speed = torrent_info.download_rate
                                # Update status if different
                                if torrent_info.status == "downloading":
                                    download.status = DownloadStatus.DOWNLOADING
                                elif torrent_info.status == "paused":
                                    download.status = DownloadStatus.PAUSED
                                elif torrent_info.progress >= 100:
                                    download.status = DownloadStatus.COMPLETED
                        except Exception:
                            pass  # Continue if we can't get torrent status
            
            return downloads
        finally:
            db.close()

    async def update_download(self, download: Download) -> Download:
        """Update a download in the database"""
        db = self._get_db()
        try:
            download_table = db.query(DownloadTable).filter(DownloadTable.id == download.id).first()
            if download_table:
                download_table.name = download.name
                download_table.status = download.status.value
                download_table.progress = download.progress
                download_table.speed = download.speed
                download_table.eta = download.eta
                download_table.queued_at = download.queued_at
                download_table.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(download_table)
                return self._download_table_to_model(download_table)
            return download
        finally:
            db.close()

    async def delete_download(self, download_id: int) -> bool:
        """Delete a download"""
        db = self._get_db()
        try:
            download_table = db.query(DownloadTable).filter(DownloadTable.id == download_id).first()
            if download_table:
                # Remove from torrent downloader if it's a torrent
                if (self.torrent_downloader and 
                    download_table.download_type == DownloadType.TORRENT.value and
                    download_id in self.download_to_torrent_map):
                    try:
                        torrent_id = self.download_to_torrent_map[download_id]
                        self.torrent_downloader.remove_download(torrent_id, False)
                        del self.download_to_torrent_map[download_id]
                        self._save_torrent_mappings()
                    except Exception:
                        pass  # Continue even if torrent removal fails
                
                db.delete(download_table)
                db.commit()
                return True
            return False
        finally:
            db.close()

    async def get_progress(self, download_id: int) -> Dict:
        """Get download progress"""
        download = await self.get_download(download_id)
        if download:
            # Try to get real-time progress from torrent downloader
            if (self.torrent_downloader and 
                download.download_type == DownloadType.TORRENT and
                download_id in self.download_to_torrent_map):
                try:
                    torrent_id = self.download_to_torrent_map[download_id]
                    torrent_info = self.torrent_downloader.get_torrent_status(torrent_id)
                    if torrent_info:
                        return {
                            "id": download.id,
                            "progress": torrent_info.progress,
                            "status": torrent_info.status,
                            "speed": torrent_info.download_rate,
                            "eta": download.eta
                        }
                except Exception:
                    pass  # Fall back to database values
            
            return {
                "id": download.id,
                "progress": download.progress,
                "status": download.status.value,
                "speed": download.speed,
                "eta": download.eta
            }
        raise Exception("Download not found")

    async def set_file_priorities(self, download_id: int, priorities: Dict[int, int]) -> Dict:
        """Set file priorities for a torrent"""
        if (self.torrent_downloader and 
            download_id in self.download_to_torrent_map):
            try:
                torrent_id = self.download_to_torrent_map[download_id]
                self.torrent_downloader.set_file_priorities(torrent_id, priorities)
                return {"message": f"File priorities set for download {download_id}"}
            except Exception as e:
                return {"error": str(e)}
        return {"message": f"File priorities set for download {download_id}"}

    async def pause_download(self, download_id: int) -> bool:
        """Pause a download"""
        download = await self.get_download(download_id)
        if download:
            # Pause in torrent downloader if it's a torrent
            if (self.torrent_downloader and 
                download.download_type == DownloadType.TORRENT and
                download_id in self.download_to_torrent_map):
                try:
                    torrent_id = self.download_to_torrent_map[download_id]
                    await self.torrent_downloader.pause_download(torrent_id)
                except Exception:
                    pass  # Continue with database update even if torrent pause fails
            
            download.status = DownloadStatus.PAUSED
            await self.update_download(download)
            return True
        return False

    async def resume_download(self, download_id: int) -> bool:
        """Resume a download"""
        download = await self.get_download(download_id)
        if download:
            # Resume in torrent downloader if it's a torrent
            if (self.torrent_downloader and 
                download.download_type == DownloadType.TORRENT and
                download_id in self.download_to_torrent_map):
                try:
                    torrent_id = self.download_to_torrent_map[download_id]
                    await self.torrent_downloader.start_download(torrent_id)
                except Exception:
                    pass  # Continue with database update even if torrent resume fails
            
            download.status = DownloadStatus.DOWNLOADING
            await self.update_download(download)
            return True
        return False

    async def add_magnet_download(self, magnet_link: str, download_path: str) -> Download:
        """Add a magnet link download (alias for add_torrent)"""
        return await self.add_torrent(magnet_link, download_path)
    
    async def add_torrent_file(self, file_upload, download_path: str) -> Download:
        """Add a torrent file download"""
        db = self._get_db()
        try:
            # Create new download record
            download_table = DownloadTable(
                url=f"file://{file_upload.filename}",
                name=file_upload.filename or f"Torrent File {datetime.now().strftime('%H:%M:%S')}",
                status=DownloadStatus.QUEUED,
                progress=0.0,
                download_type=DownloadType.TORRENT.value,
                download_path=download_path or "./downloads",
                speed=0.0,
                eta="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(download_table)
            db.commit()
            db.refresh(download_table)
            
            # TODO: Implement actual torrent file processing
            return self._download_table_to_model(download_table)
        finally:
            db.close()
    
    async def remove_download(self, download_id: int, delete_files: bool = False) -> bool:
        """Remove a download (alias for delete_download)"""
        return await self.delete_download(download_id)

    async def restart_download(self, download_id: int) -> bool:
        """Restart a download (useful for failed or legacy downloads)"""
        download = await self.get_download(download_id)
        if not download:
            return False
        
        try:
            # If it's a torrent and has a valid magnet link, try to restart it
            if (download.download_type == DownloadType.TORRENT and 
                download.url and 
                download.url.startswith('magnet:') and
                self.torrent_downloader):
                
                # Remove existing torrent if mapped
                if download_id in self.download_to_torrent_map:
                    try:
                        old_torrent_id = self.download_to_torrent_map[download_id]
                        self.torrent_downloader.remove_download(old_torrent_id, False)
                        del self.download_to_torrent_map[download_id]
                    except Exception:
                        pass  # Continue even if removal fails
                
                # Start new torrent download
                try:
                    torrent_id = await self.torrent_downloader.process_magnet_link(
                        download.url, download.download_path
                    )
                    
                    # Map download ID to new torrent ID and persist
                    self.download_to_torrent_map[download_id] = torrent_id
                    self._save_torrent_mappings()
                    
                    # Update download status
                    download.status = DownloadStatus.DOWNLOADING
                    await self.update_download(download)
                    
                    # Start the download
                    await self.torrent_downloader.start_download(torrent_id)
                    
                    return True
                except Exception as e:
                    print(f"Failed to restart torrent download {download_id}: {e}")
                    # Mark as failed
                    download.status = DownloadStatus.FAILED
                    await self.update_download(download)
                    return False
            

            # Read the NZB restart logic from file
            # Handle NZB downloads restart
            elif (download.download_type == DownloadType.NZB and 
                  download.nzb_content and 
                  self.nzb_downloader):
                
                logger.info(f"🔄 Restarting NZB download {download_id}: {download.name}")
                
                try:
                    # Reset download status
                    download.status = DownloadStatus.DOWNLOADING
                    await self.update_download(download)
                    
                    # Restart NZB download
                    success = await self.nzb_downloader.download_nzb(download_id)
                    
                    if success:
                        logger.info(f"✅ Successfully restarted NZB download {download_id}")
                        return True
                    else:
                        logger.error(f"❌ Failed to restart NZB download {download_id}")
                        download.status = DownloadStatus.FAILED
                        download.error_message = "Failed to restart NZB download"
                        await self.update_download(download)
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Error restarting NZB download {download_id}: {e}")
                    download.status = DownloadStatus.FAILED
                    download.error_message = f"Restart failed: {str(e)}"
                    await self.update_download(download)
                    return False

            # For non-torrent downloads or invalid URLs, just reset status
            if download.status in [DownloadStatus.FAILED, DownloadStatus.PAUSED]:
                download.status = DownloadStatus.QUEUED
                await self.update_download(download)
                return True
            
            return True
        except Exception as e:
            print(f"Error restarting download {download_id}: {e}")
            return False

    async def cleanup_invalid_downloads(self) -> Dict[str, int]:
        """Clean up downloads with invalid or missing URLs"""
        db = self._get_db()
        try:
            # Get all downloads
            downloads = await self.get_all_downloads()
            
            fixed_count = 0
            removed_count = 0
            
            for download in downloads:
                needs_update = False
                
                # Fix empty or null URLs
                if not download.url or download.url == "":
                    if download.download_type == DownloadType.TORRENT:
                        # Mark torrent downloads with empty URLs as failed
                        download.status = DownloadStatus.FAILED
                        needs_update = True
                    elif download.download_type == DownloadType.NZB:
                        # Set a placeholder for NZB downloads
                        download.url = f"nzb_content_{download.id}"
                        needs_update = True
                
                # Fix invalid magnet links for torrents
                elif (download.download_type == DownloadType.TORRENT and 
                      download.url and 
                      not download.url.startswith('magnet:') and
                      not download.url.startswith('nzb_content')):
                    # Invalid torrent URL
                    download.status = DownloadStatus.FAILED
                    needs_update = True
                
                if needs_update:
                    await self.update_download(download)
                    fixed_count += 1
            
            return {
                "fixed_downloads": fixed_count,
                "removed_downloads": removed_count,
                "message": f"Fixed {fixed_count} downloads"
            }
        finally:
            db.close()
