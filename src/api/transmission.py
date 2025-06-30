from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any, Optional, List
import json
import base64
from ..services_manager import services
from ..models.tables import DownloadTable as DownloadType
from ..config import settings
import asyncio
import hashlib

router = APIRouter(prefix="/api/transmission", tags=["transmission"])
download_service = services.get_download_service()

# Transmission session ID for CSRF protection
SESSION_ID = "transmission-session-id"

class TransmissionRPC:
    """Transmission RPC API compatibility layer."""
    
    def __init__(self):
        self.torrent_counter = 1000  # Start IDs from 1000
        self.torrents = {}  # Map transmission IDs to our download IDs
    
    async def handle_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Transmission RPC request."""
        method = data.get("method")
        arguments = data.get("arguments", {})
        tag = data.get("tag")
        
        try:
            if method == "session-get":
                result = await self._session_get()
            elif method == "torrent-add":
                result = await self._torrent_add(arguments)
            elif method == "torrent-get":
                result = await self._torrent_get(arguments)
            elif method == "torrent-start":
                result = await self._torrent_start(arguments)
            elif method == "torrent-stop":
                result = await self._torrent_stop(arguments)
            elif method == "torrent-remove":
                result = await self._torrent_remove(arguments)
            elif method == "torrent-set":
                result = await self._torrent_set(arguments)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
            return {
                "arguments": result,
                "result": "success",
                "tag": tag
            }
        
        except Exception as e:
            return {
                "arguments": {},
                "result": str(e),
                "tag": tag
            }
    
    async def _session_get(self) -> Dict[str, Any]:
        """Get session information."""
        return {
            "alt-speed-down": 50,
            "alt-speed-enabled": False,
            "alt-speed-time-begin": 540,
            "alt-speed-time-enabled": False,
            "alt-speed-time-end": 1020,
            "alt-speed-up": 50,
            "blocklist-enabled": False,
            "blocklist-size": 0,
            "cache-size-mb": 4,
            "config-dir": "/config",
            "download-dir": settings.DEFAULT_DOWNLOAD_PATH or "/downloads",
            "download-queue-enabled": True,
            "download-queue-size": 5,
            "dht-enabled": True,
            "encryption": "preferred",
            "idle-seeding-limit": 30,
            "idle-seeding-limit-enabled": False,
            "incomplete-dir": "/downloads/incomplete",
            "incomplete-dir-enabled": False,
            "lpd-enabled": False,
            "peer-limit-global": 200,
            "peer-limit-per-torrent": 50,
            "peer-port": 51413,
            "peer-port-random-on-start": False,
            "pex-enabled": True,
            "port-forwarding-enabled": True,
            "queue-stalled-enabled": True,
            "queue-stalled-minutes": 30,
            "rename-partial-files": True,
            "rpc-version": 15,
            "rpc-version-minimum": 1,
            "seedRatioLimit": 2,
            "seedRatioLimited": False,
            "seed-queue-enabled": False,
            "seed-queue-size": 10,
            "speed-limit-down": 100,
            "speed-limit-down-enabled": False,
            "speed-limit-up": 100,
            "speed-limit-up-enabled": False,
            "start-added-torrents": True,
            "trash-original-torrent-files": False,
            "units": {
                "memory-bytes": 1024,
                "memory-units": ["KiB", "MiB", "GiB", "TiB"],
                "size-bytes": 1000,
                "size-units": ["kB", "MB", "GB", "TB"],
                "speed-bytes": 1000,
                "speed-units": ["kB/s", "MB/s", "GB/s", "TB/s"]
            },
            "utp-enabled": True,
            "version": "3.00 (media-downloader-compat)"
        }
    
    async def _torrent_add(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new torrent."""
        filename = arguments.get("filename")  # Magnet link
        metainfo = arguments.get("metainfo")  # Base64 encoded torrent file
        download_dir = arguments.get("download-dir", settings.DEFAULT_DOWNLOAD_PATH)
        
        try:
            if filename:  # Magnet link
                download = await download_service.add_magnet_download(
                    magnet_link=filename,
                    download_path=download_dir or settings.DEFAULT_DOWNLOAD_PATH
                )
            elif metainfo:  # Torrent file
                # Decode base64 torrent data
                torrent_data = base64.b64decode(metainfo)
                # For now, we'll save it as a temp file and process
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".torrent") as f:
                    f.write(torrent_data)
                    temp_path = f.name
                
                try:
                    # Process torrent file (you'd implement this in download_service)
                    download = await download_service.add_torrent_file(
                        file_path=temp_path,
                        download_path=download_dir or settings.DEFAULT_DOWNLOAD_PATH
                    )
                finally:
                    os.unlink(temp_path)
            else:
                raise ValueError("No filename or metainfo provided")
            
            # Generate transmission-compatible ID
            transmission_id = self.torrent_counter
            self.torrent_counter += 1
            self.torrents[transmission_id] = download.id
            
            # Generate info hash (simplified)
            info_hash = hashlib.sha1(str(download.id).encode()).hexdigest()
            
            return {
                "torrent-added": {
                    "hashString": info_hash,
                    "id": transmission_id,
                    "name": download.name or "Unknown"
                }
            }
        
        except Exception as e:
            return {
                "torrent-duplicate": {
                    "hashString": "",
                    "id": 0,
                    "name": str(e)
                }
            }
    
    async def _torrent_get(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get torrent information."""
        ids = arguments.get("ids", [])
        fields = arguments.get("fields", [])
        
        torrents = []
        
        # If no IDs specified, get all
        if not ids:
            ids = list(self.torrents.keys())
        
        for transmission_id in ids:
            if transmission_id in self.torrents:
                download_id = self.torrents[transmission_id]
                try:
                    download = await download_service.get_download(download_id)
                    if download:
                        torrent_info = await self._format_torrent_info(download, transmission_id, fields)
                        torrents.append(torrent_info)
                except Exception:
                    continue
        
        return {"torrents": torrents}
    
    async def _format_torrent_info(self, download, transmission_id: int, fields: List[str]) -> Dict[str, Any]:
        """Format download info as Transmission torrent info."""
        # Map our download status to Transmission status
        status_map = {
            "downloading": 4,  # TR_STATUS_DOWNLOAD
            "paused": 0,       # TR_STATUS_STOPPED
            "completed": 6,    # TR_STATUS_SEED
            "error": 3,        # TR_STATUS_DOWNLOAD_WAIT
            "queued": 3        # TR_STATUS_DOWNLOAD_WAIT
        }
        
        info = {
            "id": transmission_id,
            "name": download.name or "Unknown",
            "hashString": hashlib.sha1(str(download.id).encode()).hexdigest(),
            "status": status_map.get(download.status, 0),
            "downloadDir": download.download_path or settings.DEFAULT_DOWNLOAD_PATH,
            "isFinished": download.status == "completed",
            "percentDone": (download.progress or 0) / 100.0,
            "rateDownload": 0,  # We don't track this currently
            "rateUpload": 0,   # We don't track this currently
            "sizeWhenDone": download.size or 0,
            "totalSize": download.size or 0,
            "downloadedEver": int((download.size or 0) * (download.progress or 0) / 100),
            "uploadedEver": 0,
            "eta": -1,  # Unknown
            "peersConnected": 0,
            "peersGettingFromUs": 0,
            "peersSendingToUs": 0,
            "seedRatioLimit": 2.0,
            "seedRatioMode": 0,
            "addedDate": int(download.created_at.timestamp()) if download.created_at else 0,
            "activityDate": int(download.updated_at.timestamp()) if download.updated_at else 0,
            "error": 0,
            "errorString": "",
            "files": [],
            "fileStats": [],
            "priorities": [],
            "wanted": []
        }
        
        # Filter fields if specified
        if fields:
            filtered_info = {}
            for field in fields:
                if field in info:
                    filtered_info[field] = info[field]
            return filtered_info
        
        return info
    
    async def _torrent_start(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Start torrents."""
        ids = arguments.get("ids", [])
        
        for transmission_id in ids:
            if transmission_id in self.torrents:
                download_id = self.torrents[transmission_id]
                try:
                    await download_service.resume_download(download_id)
                except Exception:
                    continue
        
        return {}
    
    async def _torrent_stop(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Stop torrents."""
        ids = arguments.get("ids", [])
        
        for transmission_id in ids:
            if transmission_id in self.torrents:
                download_id = self.torrents[transmission_id]
                try:
                    await download_service.pause_download(download_id)
                except Exception:
                    continue
        
        return {}
    
    async def _torrent_remove(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Remove torrents."""
        ids = arguments.get("ids", [])
        delete_local_data = arguments.get("delete-local-data", False)
        
        for transmission_id in ids:
            if transmission_id in self.torrents:
                download_id = self.torrents[transmission_id]
                try:
                    await download_service.remove_download(download_id, delete_files=delete_local_data)
                    del self.torrents[transmission_id]
                except Exception:
                    continue
        
        return {}
    
    async def _torrent_set(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Set torrent properties."""
        # For now, just acknowledge the request
        # You could implement priority changes, download directory changes, etc.
        return {}

# Global RPC handler instance
rpc_handler = TransmissionRPC()

@router.post("/rpc")
async def transmission_rpc(
    request: Request,
    x_transmission_session_id: Optional[str] = Header(None)
):
    """Transmission RPC endpoint."""
    try:
        # Parse JSON-RPC request
        body = await request.body()
        data = json.loads(body)
        
        # Handle the RPC request
        response = await rpc_handler.handle_request(data)
        
        return response
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rpc")
async def transmission_rpc_get():
    """Handle GET requests to RPC endpoint (returns session info)."""
    return await rpc_handler._session_get()

@router.get("/client-config")
async def get_client_configuration():
    """Get the configuration details for adding this as a download client in media managers."""
    return {
        "transmission": {
            "name": "Media Downloader",
            "implementation": "Transmission",
            "host": "localhost",
            "port": 8000,
            "url_base": "/api/transmission/rpc",
            "username": "",
            "password": "",
            "category": "media-downloader",
            "full_url": "http://localhost:8000/api/transmission/rpc",
            "instructions": {
                "readarr": [
                    "1. Go to Settings → Download Clients in Readarr",
                    "2. Click the '+' button to add a new download client",
                    "3. Select 'Transmission' from the list",
                    "4. Fill in the following details:",
                    "   - Name: Media Downloader",
                    "   - Host: localhost",
                    "   - Port: 8000",
                    "   - URL Base: /api/transmission/rpc",
                    "   - Username: (leave blank)",
                    "   - Password: (leave blank)",
                    "   - Category: readarr",
                    "5. Click 'Test' to verify connection",
                    "6. Click 'Save' to add the download client"
                ],
                "sonarr": [
                    "1. Go to Settings → Download Clients in Sonarr",
                    "2. Click the '+' button to add a new download client",
                    "3. Select 'Transmission' from the list",
                    "4. Fill in the following details:",
                    "   - Name: Media Downloader",
                    "   - Host: localhost",
                    "   - Port: 8000",
                    "   - URL Base: /api/transmission/rpc",
                    "   - Username: (leave blank)",
                    "   - Password: (leave blank)",
                    "   - Category: sonarr",
                    "5. Click 'Test' to verify connection",
                    "6. Click 'Save' to add the download client"
                ],
                "radarr": [
                    "1. Go to Settings → Download Clients in Radarr",
                    "2. Click the '+' button to add a new download client",
                    "3. Select 'Transmission' from the list",
                    "4. Fill in the following details:",
                    "   - Name: Media Downloader",
                    "   - Host: localhost",
                    "   - Port: 8000",
                    "   - URL Base: /api/transmission/rpc",
                    "   - Username: (leave blank)",
                    "   - Password: (leave blank)",
                    "   - Category: radarr",
                    "5. Click 'Test' to verify connection",
                    "6. Click 'Save' to add the download client"
                ]
            }
        },
        "json_config": {
            "description": "JSON configuration for API-based setup",
            "readarr": {
                "name": "Media Downloader",
                "implementation": "Transmission",
                "configContract": "TransmissionSettings",
                "enable": True,
                "protocol": "torrent",
                "priority": 1,
                "removeCompletedDownloads": False,
                "removeFailedDownloads": True,
                "fields": [
                    {"name": "host", "value": "localhost"},
                    {"name": "port", "value": 8000},
                    {"name": "urlBase", "value": "/api/transmission/rpc"},
                    {"name": "username", "value": ""},
                    {"name": "password", "value": ""},
                    {"name": "musicCategory", "value": "readarr"},
                    {"name": "musicDirectory", "value": ""},
                    {"name": "recentTvPriority", "value": 2},
                    {"name": "olderTvPriority", "value": 2},
                    {"name": "addStopped", "value": False}
                ]
            },
            "sonarr": {
                "name": "Media Downloader",
                "implementation": "Transmission",
                "configContract": "TransmissionSettings",
                "enable": True,
                "protocol": "torrent",
                "priority": 1,
                "removeCompletedDownloads": False,
                "removeFailedDownloads": True,
                "settings": {
                    "host": "localhost",
                    "port": 8000,
                    "urlBase": "/api/transmission/rpc",
                    "username": "",
                    "password": "",
                    "tvCategory": "sonarr",
                    "tvDirectory": "",
                    "recentTvPriority": 2,
                    "olderTvPriority": 2,
                    "addStopped": False
                }
            },
            "radarr": {
                "name": "Media Downloader",
                "implementation": "Transmission",
                "configContract": "TransmissionSettings",
                "enable": True,
                "protocol": "torrent",
                "priority": 1,
                "removeCompletedDownloads": False,
                "removeFailedDownloads": True,
                "settings": {
                    "host": "localhost",
                    "port": 8000,
                    "urlBase": "/api/transmission/rpc",
                    "username": "",
                    "password": "",
                    "movieCategory": "radarr",
                    "movieDirectory": "",
                    "recentMoviePriority": 2,
                    "olderMoviePriority": 2,
                    "addStopped": False
                }
            }
        }
    }

