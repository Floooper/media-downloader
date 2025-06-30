import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from ..models.tables import DownloadTable as Download, DownloadStatus, DownloadType
from ..config import settings

class QueueManager:
    def __init__(self):
        # Remove in-memory storage, use download service instead
        self.max_concurrent = settings.MAX_CONCURRENT_DOWNLOADS
        self.download_service = None  # Will be set after initialization

    def set_download_service(self, service):
        self.download_service = service

    
    async def get_queue(self) -> List[Download]:
        """Get all downloads (queue + active + completed)"""
        if self.download_service:
            return await self.download_service.get_all_downloads()
        return []

    async def add_to_queue(self, download: Download) -> Download:
        """Add a download to the queue and start it if possible."""
        download.queued_at = datetime.utcnow()
        download.status = DownloadStatus.QUEUED
        
        # Update in database
        download = await self.download_service.update_download(download)
        
        # Process queue to start downloads if slots available
        await self._process_queue()
        
        return download

    async def remove_from_queue(self, download_id: int) -> bool:
        """Remove a download from the queue."""
        download = await self.download_service.get_download(download_id)
        if download:
            success = await self.download_service.remove_download(download_id, delete_files=False)
            return success
        return False

    async def pause_download(self, download_id: int) -> Optional[Download]:
        """Pause a download."""
        success = await self.download_service.pause_download(download_id)
        if success:
            await self._process_queue()  # Start next download if slot available
            return await self.download_service.get_download(download_id)
        return None

    async def resume_download(self, download_id: int) -> Optional[Download]:
        """Resume a paused download."""
        success = await self.download_service.resume_download(download_id)
        if success:
            await self._process_queue()
            return await self.download_service.get_download(download_id)
        return None

    async def _process_queue(self):
        """Process the queue and start downloads if possible."""
        if not self.download_service:
            return
        
        # Get all downloads
        all_downloads = await self.download_service.get_all_downloads()
        
        # Count active downloads
        active_downloads = [d for d in all_downloads if d.status == DownloadStatus.DOWNLOADING]
        queued_downloads = [d for d in all_downloads if d.status == DownloadStatus.QUEUED]
        
        # Start downloads if we have available slots
        available_slots = self.max_concurrent - len(active_downloads)
        
        for i in range(min(available_slots, len(queued_downloads))):
            download = queued_downloads[i]
            download.status = DownloadStatus.DOWNLOADING
            download.updated_at = datetime.utcnow()
            await self.download_service.update_download(download)

    async def get_queue_status(self) -> Dict:
        """Get current queue status."""
        if not self.download_service:
            return {
                "active_downloads": 0,
                "queued_downloads": 0,
                "paused_downloads": 0,
                "max_concurrent": self.max_concurrent
            }
        
        all_downloads = await self.download_service.get_all_downloads()
        
        active_count = len([d for d in all_downloads if d.status == DownloadStatus.DOWNLOADING])
        queued_count = len([d for d in all_downloads if d.status == DownloadStatus.QUEUED])
        paused_count = len([d for d in all_downloads if d.status == DownloadStatus.PAUSED])
        
        return {
            "active_downloads": active_count,
            "queued_downloads": queued_count,
            "paused_downloads": paused_count,
            "max_concurrent": self.max_concurrent
        }

    async def move_up(self, download_id: int) -> bool:
        """Move a download up in the queue (simplified implementation)."""
        # For now, just return True since we don't have queue ordering in the database
        # This would require a queue_position field in the database
        return True

    async def move_down(self, download_id: int) -> bool:
        """Move a download down in the queue (simplified implementation)."""
        # For now, just return True since we don't have queue ordering in the database  
        # This would require a queue_position field in the database
        return True

    async def set_position(self, download_id: int, new_position: int) -> bool:
        """Set a download to a specific position in the queue (simplified implementation)."""
        # For now, just return True since we don't have queue ordering in the database
        # This would require a queue_position field in the database
        return True

    async def clear_queue(self) -> int:
        """Clear all queued downloads."""
        if not self.download_service:
            return 0
        
        all_downloads = await self.download_service.get_all_downloads()
        queued_downloads = [d for d in all_downloads if d.status == DownloadStatus.QUEUED]
        
        count = 0
        for download in queued_downloads:
            success = await self.download_service.remove_download(download.id, delete_files=False)
            if success:
                count += 1
        
        return count
