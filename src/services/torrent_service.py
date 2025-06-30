"""
Real Torrent Service using libtorrent-python
"""
import asyncio
import os
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
    print("✅ Using real libtorrent implementation")
except ImportError:
    LIBTORRENT_AVAILABLE = False
    print("❌ libtorrent not available, falling back to mock implementation")

@dataclass
class TorrentFile:
    path: str
    size: int
    priority: int
    progress: float = 0.0

@dataclass
class TorrentInfo:
    name: str
    total_size: int
    files: List[TorrentFile]
    progress: float = 0.0
    download_rate: int = 0  # bytes/sec
    upload_rate: int = 0    # bytes/sec
    num_peers: int = 0
    status: str = "unknown"

class TorrentDownloader:
    """Auto-selecting torrent downloader"""
    def __init__(self, 
                 max_connections_per_torrent: int = 50,
                 max_upload_rate: int = 0,
                 max_download_rate: int = 0,
                 listen_port: int = 6881):
        
        if LIBTORRENT_AVAILABLE:
            print("✅ Initializing real libtorrent downloader")
            self._init_libtorrent(max_connections_per_torrent, max_upload_rate, max_download_rate, listen_port)
        else:
            print("WARNING: Using mock torrent downloader. Install libtorrent for real functionality.")
            self._init_mock()
    
    def _init_libtorrent(self, max_connections_per_torrent, max_upload_rate, max_download_rate, listen_port):
        """Initialize real libtorrent session"""
        self.session = lt.session()
        
        settings = {
            'connections_limit': max_connections_per_torrent * 10,
            'upload_rate_limit': max_upload_rate,
            'download_rate_limit': max_download_rate,
            'listen_interfaces': f'0.0.0.0:{listen_port}',
            'enable_dht': True,
            'enable_lsd': True,
        }
        self.session.apply_settings(settings)
        self.session.add_dht_router("router.bittorrent.com", 6881)
        
        self.handles: Dict[str, lt.torrent_handle] = {}
        self.download_ids: Dict[str, str] = {}
        
    def _init_mock(self):
        """Initialize mock implementation"""
        self.active_torrents: Dict[str, dict] = {}
        self.torrent_info: Dict[str, TorrentInfo] = {}

    async def process_magnet_link(self, magnet_link: str, save_path: str) -> str:
        """Process a magnet link"""
        if LIBTORRENT_AVAILABLE:
            return await self._process_magnet_real(magnet_link, save_path)
        else:
            return await self._process_magnet_mock(magnet_link, save_path)
    
    async def _process_magnet_real(self, magnet_link: str, save_path: str) -> str:
        """Process magnet with libtorrent"""
        try:
            add_torrent_params = lt.parse_magnet_uri(magnet_link)
            add_torrent_params.save_path = save_path
            
            handle = self.session.add_torrent(add_torrent_params)
            info_hash = str(handle.info_hash())
            download_id = f"lt_{hash(info_hash) % 100000}"
            
            self.handles[download_id] = handle
            self.download_ids[info_hash] = download_id
            
            print(f"✅ Added torrent: {download_id}")
            return download_id
            
        except Exception as e:
            print(f"❌ Error processing magnet link: {e}")
            raise Exception(f"Failed to process magnet link: {e}")
    
    async def _process_magnet_mock(self, magnet_link: str, save_path: str) -> str:
        """Mock process a magnet link"""
        download_id = f"mock_{hash(magnet_link) % 10000}"
        
        self.torrent_info[download_id] = TorrentInfo(
            name=f"Mock Download {datetime.now().strftime('%H:%M:%S')}",
            total_size=1024 * 1024 * 100,  # 100MB mock size
            files=[
                TorrentFile(
                    path="mock_file.mp4",
                    size=1024 * 1024 * 100,
                    priority=1,
                    progress=0.0
                )
            ],
            progress=0.0,
            download_rate=1024 * 512,  # 512KB/s mock speed
            upload_rate=1024 * 128,    # 128KB/s mock upload
            num_peers=5,
            status="downloading"
        )
        
        self.active_torrents[download_id] = {"status": "downloading"}
        return download_id

    def get_torrent_status(self, download_id: str) -> Optional[TorrentInfo]:
        """Get torrent status"""
        if LIBTORRENT_AVAILABLE and download_id in self.handles:
            return self._get_status_real(download_id)
        else:
            return self.torrent_info.get(download_id)
    
    def _get_status_real(self, download_id: str) -> Optional[TorrentInfo]:
        """Get real torrent status"""
        try:
            handle = self.handles[download_id]
            status = handle.status()
            
            state_map = {
                lt.torrent_status.downloading: "downloading",
                lt.torrent_status.finished: "completed",
                lt.torrent_status.seeding: "seeding",
                lt.torrent_status.queued_for_checking: "queued",
            }
            
            torrent_status = state_map.get(status.state, "unknown")
            
            files = []
            if handle.has_metadata():
                torrent_info = handle.get_torrent_info()
                name = torrent_info.name()
                total_size = torrent_info.total_size()
            else:
                name = f"Downloading metadata... ({download_id})"
                total_size = status.total_wanted or 0
            
            return TorrentInfo(
                name=name,
                total_size=total_size,
                files=files,
                progress=status.progress * 100.0,
                download_rate=status.download_rate,
                upload_rate=status.upload_rate,
                num_peers=status.num_peers,
                status=torrent_status
            )
            
        except Exception as e:
            print(f"❌ Error getting torrent status: {e}")
            return None

    def pause_torrent(self, download_id: str) -> bool:
        """Pause a torrent"""
        if LIBTORRENT_AVAILABLE and download_id in self.handles:
            try:
                self.handles[download_id].pause()
                return True
            except Exception:
                return False
        elif download_id in self.active_torrents:
            self.active_torrents[download_id]["status"] = "paused"
            if download_id in self.torrent_info:
                self.torrent_info[download_id].status = "paused"
            return True
        return False

    def resume_torrent(self, download_id: str) -> bool:
        """Resume a torrent"""
        if LIBTORRENT_AVAILABLE and download_id in self.handles:
            try:
                self.handles[download_id].resume()
                return True
            except Exception:
                return False
        elif download_id in self.active_torrents:
            self.active_torrents[download_id]["status"] = "downloading"
            if download_id in self.torrent_info:
                self.torrent_info[download_id].status = "downloading"
            return True
        return False

    def remove_torrent(self, download_id: str, delete_files: bool = False) -> bool:
        """Remove a torrent"""
        if LIBTORRENT_AVAILABLE and download_id in self.handles:
            try:
                handle = self.handles[download_id]
                info_hash = str(handle.info_hash())
                
                if delete_files:
                    self.session.remove_torrent(handle, lt.session.delete_files)
                else:
                    self.session.remove_torrent(handle)
                
                del self.handles[download_id]
                if info_hash in self.download_ids:
                    del self.download_ids[info_hash]
                return True
            except Exception:
                return False
        elif download_id in self.active_torrents:
            del self.active_torrents[download_id]
            if download_id in self.torrent_info:
                del self.torrent_info[download_id]
            return True
        return False
