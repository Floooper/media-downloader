"""
Service Manager - Provides singleton instances of services
"""
from typing import Dict, Any, Optional
from .services.download_service import DownloadService
from .services.queue_service import QueueManager
from .services.tag_service import TagService 
from .services.torrent_service import TorrentDownloader

class ServicesManager:
    """Singleton manager for all services"""
    _instance = None
    _download_service = None
    _queue_manager = None
    _tag_service = None
    _torrent_downloader = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServicesManager, cls).__new__(cls)
        return cls._instance
    
    def get_download_service(self) -> DownloadService:
        """Get the singleton download service instance"""
        if self._download_service is None:
            self._download_service = DownloadService()
            # Inject torrent downloader into download service
            self._download_service.set_torrent_downloader(self.get_torrent_downloader())
            self._download_service.set_nzb_downloader(self.get_nzb_downloader())
        return self._download_service
    
    def get_queue_manager(self) -> QueueManager:
        """Get the singleton queue manager instance"""
        if self._queue_manager is None:
            self._queue_manager = QueueManager()
            # Link with download service
            self._queue_manager.set_download_service(self.get_download_service())
        return self._queue_manager
    
    def get_tag_service(self) -> TagService:
        """Get the singleton tag service instance"""
        if self._tag_service is None:
            self._tag_service = TagService()
        return self._tag_service
    
    def get_torrent_downloader(self) -> TorrentDownloader:
        """Get the singleton torrent downloader instance"""
        if self._torrent_downloader is None:
            self._torrent_downloader = TorrentDownloader()
        return self._torrent_downloader

    def get_nzb_downloader(self):
        """Get the singleton NZB downloader instance"""
        if not hasattr(self, "_nzb_downloader"):
            from .services.nzb_service import NZBService
            from .config import settings
            
            config = {
                "host": settings.USENET_SERVER,
                "port": settings.USENET_PORT,
                "ssl": settings.USENET_SSL,
                "username": settings.USENET_USERNAME,
                "password": settings.USENET_PASSWORD,
                "max_connections": settings.USENET_MAX_CONNECTIONS,
                "retention_days": settings.USENET_RETENTION_DAYS,
                "download_rate_limit": settings.USENET_DOWNLOAD_RATE_LIMIT,
                "max_retries": settings.USENET_MAX_RETRIES
            }
            
            # Initialize NZB service with config dictionary
            self._nzb_downloader = NZBService(config)
            
            # Log the configuration being used (mask password)
            masked_password = "***" if settings.USENET_PASSWORD else "(empty)"
            logger.info(f"🔧 NZB downloader initialized with current settings:")
            logger.info(f"   Server: {settings.USENET_SERVER}:{settings.USENET_PORT}")
            logger.info(f"   SSL: {settings.USENET_SSL}")
            logger.info(f"   Username: {settings.USENET_USERNAME}")
            logger.info(f"   Password: {masked_password}")
            
        return self._nzb_downloader

# Global singleton instance  
services = ServicesManager()
